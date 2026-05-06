"""
app/services/llm/client_factory — Centralized Anthropic SDK client factory.

Provides:
  get_anthropic_api_key() -> str   — unwraps SecretStr safely
  get_anthropic_client() -> AsyncAnthropic — pre-configured client instance

Single chokepoint for all SDK construction. Eliminates the class of bug
where a SecretStr is passed directly to the Anthropic SDK (which accepts Any
at runtime but fails on first HTTP call).
"""

from __future__ import annotations


def get_anthropic_api_key() -> str:
    """
    Return the Anthropic API key as a plain str.

    Unwraps pydantic SecretStr via .get_secret_value() so callers never
    pass SecretStr directly to an SDK boundary.
    """
    from config import settings  # local import avoids circular imports at module load

    return settings.anthropic_api_key.get_secret_value()


def get_anthropic_client():
    """
    Return a configured AsyncAnthropic client.

    Returns:
        anthropic.AsyncAnthropic instance ready for use.
    """
    import anthropic

    return anthropic.AsyncAnthropic(api_key=get_anthropic_api_key())
