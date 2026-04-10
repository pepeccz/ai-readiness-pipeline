"""
Shared Anthropic client and utilities for LLM enrichers.
Provides singleton client, call_llm with model fallback, and JSON extraction with repair.
"""

import os
import json
import anthropic

# --- Config ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL_PRIMARY = "claude-sonnet-4-5-20250514"
MODEL_FALLBACK = "claude-haiku-4-5-20251001"

# --- Client singleton ---
_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    """Return singleton Anthropic client. Create on first call."""
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY no configurado")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def call_llm(
    system_blocks: list[dict],
    user_content: str,
    model: str = MODEL_PRIMARY,
    fallback_model: str | None = MODEL_FALLBACK,
    temperature: float = 0.3,
    max_tokens: int = 8000,
    max_tokens_fallback: int = 4096,
) -> str:
    """
    Call Anthropic API with model fallback.

    system_blocks: list of content blocks with optional cache_control.
      Example: [{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}]
    Returns raw text content from the model.
    Raises ValueError if all models fail.
    """
    client = get_client()
    models_to_try = [model]
    if fallback_model:
        models_to_try.append(fallback_model)
    last_error = None

    for m in models_to_try:
        try:
            print(f"   [llm_client] Intentando con modelo: {m}")
            tokens = max_tokens if m == model else max_tokens_fallback
            response = client.messages.create(
                model=m,
                system=system_blocks,
                messages=[{"role": "user", "content": user_content}],
                temperature=temperature,
                max_tokens=tokens,
            )
            print(f"   [llm_client] Éxito con modelo: {m}")

            # Log cache metrics if available
            usage = response.usage
            cache_created = getattr(usage, "cache_creation_input_tokens", None)
            cache_read = getattr(usage, "cache_read_input_tokens", None)
            if cache_created is not None or cache_read is not None:
                print(
                    f"   [llm_client] Cache: created={cache_created or 0}, read={cache_read or 0}"
                )

            return response.content[0].text
        except Exception as e:
            print(f"   [llm_client] Error con {m}: {e}")
            last_error = e
            if m == models_to_try[-1]:
                raise ValueError(f"Todos los modelos fallaron. Último error: {last_error}")
            continue


def extract_json(content: str) -> dict:
    """
    Extract and parse JSON from LLM response.
    Handles markdown code blocks, leading text, and truncated JSON.
    Returns parsed dict.
    Raises json.JSONDecodeError if unrecoverable.
    """
    content = content.strip()

    # Remove markdown code block wrappers
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # Find the JSON object boundaries
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1:
        content = content[start : end + 1]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Attempt repair: close unclosed braces/brackets
        print("   [llm_client] JSON incompleto, intentando reparar...")
        opens = content.count("{") - content.count("}")
        closes = content.count("[") - content.count("]")
        content += "]" * max(0, closes) + "}" * max(0, opens)
        return json.loads(content)
