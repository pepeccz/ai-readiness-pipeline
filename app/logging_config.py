"""
app/logging_config — Structured logging configuration.

Library choice: structlog (over stdlib JSON formatter).
Rationale:
  - structlog.get_logger(__name__) is the exact API the design specifies
  - JSON output works out of the box — no custom Formatter subclass needed
  - contextvars support is built-in: bind_contextvars(request_id=...) and every
    subsequent log line in the same async task carries it automatically
  - stdlib logging bridge (structlog.stdlib.ProcessorFormatter) means existing
    uvicorn / SQLAlchemy log lines get the same JSON treatment

Usage (in any module):
  import structlog
  logger = structlog.get_logger(__name__)
  logger.info("assessment_received", assessment_id=str(id), company=name)

RequestIdMiddleware:
  Generates a UUID per request, binds it to contextvars so all log lines
  produced during that request automatically include `request_id`.
  Also logs one line at request start and one at response return.
"""

import logging
import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar to carry the request_id across async boundaries within a single request.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog + stdlib logging once at application startup.

    Call this BEFORE the FastAPI app processes any requests. In webhook_service.py
    this is called at module level, immediately after `app = FastAPI(...)`.

    In development (non-JSON terminals), you can set log_level="DEBUG" via env var
    and structlog will still output valid JSON — pipe through `jq` for readability.
    """
    # 1. Shared processors: applied to every log event regardless of source
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,         # injects request_id etc.
        structlog.stdlib.add_logger_name,                # adds "logger" key
        structlog.stdlib.add_log_level,                  # adds "level" key
        structlog.processors.TimeStamper(fmt="iso"),     # adds "timestamp" key (ISO-8601 UTC)
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 2. Configure structlog itself
    # Use stdlib LoggerFactory + BoundLogger so add_logger_name (which needs
    # logger.name) works. PrintLoggerFactory's PrintLogger has no .name attr.
    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 3. Bridge stdlib logging (uvicorn, SQLAlchemy, etc.) through structlog
    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    )
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Silence overly verbose loggers that don't add value in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that assigns a UUID to every HTTP request and binds
    it to structlog's contextvars so all log lines produced during the request
    automatically include `request_id`, `method`, and `path`.

    Logs one line at request entry and one at response exit (with status_code).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = uuid.uuid4().hex

        # Bind to structlog context for this async task tree
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger = structlog.get_logger("http")
        logger.info("request_started")

        response = await call_next(request)

        logger.info("request_finished", status_code=response.status_code)

        # Expose request_id in response header for client-side correlation
        response.headers["X-Request-Id"] = request_id

        return response
