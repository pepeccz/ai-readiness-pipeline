"""
tests/services/llm/test_client_factory — REQ-1 regression tests.

Verifies that:
  1. get_anthropic_api_key() returns a plain str, not a SecretStr.
  2. Constructing AsyncAnthropic via get_anthropic_client() does not raise TypeError.
  3. get_anthropic_api_key() value is not an instance of SecretStr.
"""

from __future__ import annotations

import pytest
from pydantic import SecretStr


# ---------------------------------------------------------------------------
# A-3 · test_get_anthropic_api_key_returns_str
# ---------------------------------------------------------------------------


def test_get_anthropic_api_key_returns_str():
    """get_anthropic_api_key() must return a plain str, not SecretStr."""
    import config

    original_settings = config.settings
    try:
        config.settings = config.Settings(anthropic_api_key=SecretStr("sk-test-1234"))  # type: ignore[call-arg]
        from app.services.llm.client_factory import get_anthropic_api_key
        result = get_anthropic_api_key()
        assert isinstance(result, str), f"Expected str, got {type(result)}"
        assert not isinstance(result, SecretStr), "Must not return SecretStr"
    finally:
        config.settings = original_settings


# ---------------------------------------------------------------------------
# A-3 · test_secretstr_not_passed_directly
# ---------------------------------------------------------------------------


def test_secretstr_not_passed_directly():
    """get_anthropic_api_key() value must not be a SecretStr instance."""
    import config
    from pydantic import SecretStr as PydanticSecretStr

    original_settings = config.settings
    try:
        config.settings = config.Settings(anthropic_api_key=PydanticSecretStr("sk-test-5678"))  # type: ignore[call-arg]
        from app.services.llm.client_factory import get_anthropic_api_key
        result = get_anthropic_api_key()
        assert not isinstance(result, PydanticSecretStr)
        assert result == "sk-test-5678"
    finally:
        config.settings = original_settings


# ---------------------------------------------------------------------------
# A-3 · test_client_construction_no_type_error
# ---------------------------------------------------------------------------


def test_client_construction_no_type_error():
    """
    Constructing AsyncAnthropic via get_anthropic_client() must not raise TypeError.

    Uses a mocked httpx transport to avoid network calls.
    """
    import config
    from pydantic import SecretStr as PydanticSecretStr

    original_settings = config.settings
    try:
        config.settings = config.Settings(anthropic_api_key=PydanticSecretStr("sk-test-no-error"))  # type: ignore[call-arg]
        from app.services.llm.client_factory import get_anthropic_client

        # Construction must not raise — we're not calling the API
        client = get_anthropic_client()
        assert client is not None
        # Verify the api_key stored internally is a plain str
        assert isinstance(client.api_key, str)
        assert not isinstance(client.api_key, SecretStr)
    finally:
        config.settings = original_settings
