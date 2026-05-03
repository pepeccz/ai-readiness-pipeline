"""
app/schemas/common — Shared error envelope and exception types.

All API error responses follow the shape:
  {"detail": "<human-readable message>", "code": "<machine-readable code>"}

Usage:
  raise ApiException(status_code=401, code="not_authenticated", detail="Login required")

Registration (call once in webhook_service.py):
  from app.schemas.common import add_error_handlers
  add_error_handlers(app)
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all API error responses."""

    detail: str
    code: str


class ApiException(Exception):
    """
    Raise this anywhere in the app to return a consistent error envelope.

    Example:
      raise ApiException(status_code=401, code="not_authenticated", detail="Login required")
    """

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        self.status_code = status_code
        self.code = code
        self.detail = detail
        super().__init__(detail)


# Substring-to-error-code mapping for Pydantic validation errors raised by
# AssessmentPatch model_validators (TASK-IN-08).
# Keys are stable prefix substrings from the validator ValueError messages;
# values are the machine-readable error codes returned in the 422 envelope.
# Order matters: the first match wins.
_VALIDATION_ERROR_CODE_MAP: dict[str, str] = {
    # From AssessmentPatch._validate_form_data_exclusivity
    "form_data and form_data_patch are mutually exclusive": "form_data_conflict",
    # From AssessmentPatch._validate_form_data_patch_keys
    "Unknown form_data key:": "unknown_form_data_key",
}


def add_error_handlers(app: FastAPI) -> None:
    """
    Register exception handlers on the FastAPI app instance.

    Call this once in webhook_service.py immediately after creating `app`.
    Three handlers are registered:
      1. ApiException      — our own typed exceptions → {detail, code}
      2. HTTPException     — FastAPI/Starlette built-ins → {detail, code: "http_error"}
      3. RequestValidationError — Pydantic 422 validation failures → {detail, code}
         The code is derived by substring-matching validator messages against
         _VALIDATION_ERROR_CODE_MAP; falls back to "validation_error".
    """

    @app.exception_handler(ApiException)
    async def _api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": exc.code},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Preserve the original status code; wrap the detail in the envelope.
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail, "code": "http_error"},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        # Flatten Pydantic errors into a single human-readable string.
        messages = "; ".join(
            f"{' -> '.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in errors
        )
        # Derive a specific error code by scanning all error messages for known
        # validator substrings.  First match wins; falls back to "validation_error".
        code = "validation_error"
        for err in errors:
            msg = err.get("msg", "")
            matched = next(
                (c for substring, c in _VALIDATION_ERROR_CODE_MAP.items() if substring in msg),
                None,
            )
            if matched is not None:
                code = matched
                break
        return JSONResponse(
            status_code=422,
            content={"detail": messages, "code": code},
        )
