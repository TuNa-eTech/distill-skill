"""Provider-pluggable LLM client.

Public API: ``complete(system=..., user=..., ...)`` returns a string.

Provider is selected at call time via the ``LLM_PROVIDER`` env var
(default ``openai``). MVP only implements the OpenAI/GPT provider; the
Anthropic stub raises with explicit instructions for enabling it.
"""
import json
import re
from typing import Any, Callable

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import env, llm_model

_DEFAULT_PROVIDER = "openai"


def _provider() -> str:
    return env("LLM_PROVIDER", _DEFAULT_PROVIDER) or _DEFAULT_PROVIDER


# ---------- OpenAI / GPT ----------

def _openai_client() -> OpenAI:
    return OpenAI(api_key=env("GPT_API_KEY", required=True))


def _complete_openai(
    *, system: str, user: str, max_tokens: int, model: str | None, temperature: float
) -> str:
    resp = _openai_client().chat.completions.create(
        model=model or llm_model(),
        max_completion_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""


# ---------- Anthropic / Claude (stub for future) ----------

def _complete_anthropic(
    *, system: str, user: str, max_tokens: int, model: str | None, temperature: float
) -> str:
    raise NotImplementedError(
        "Anthropic provider not implemented in MVP. To enable:\n"
        "  1. pip install anthropic>=0.40.0\n"
        "  2. Implement this function with Anthropic().messages.create(...)\n"
        "  3. Set LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env\n"
        "  4. Optionally set ANTHROPIC_MODEL (default falls back to GPT_MODEL)."
    )


_PROVIDERS: dict[str, Callable[..., str]] = {
    "openai": _complete_openai,
    "anthropic": _complete_anthropic,
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
def complete(
    *,
    system: str,
    user: str,
    max_tokens: int = 2000,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    provider = _provider()
    if provider not in _PROVIDERS:
        raise RuntimeError(
            f"Unknown LLM_PROVIDER: {provider!r}. Supported: {sorted(_PROVIDERS)}"
        )
    return _PROVIDERS[provider](
        system=system,
        user=user,
        max_tokens=max_tokens,
        model=model,
        temperature=temperature,
    )


# ---------- helpers ----------

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> Any:
    match = _JSON_FENCE.search(text)
    payload = match.group(1) if match else text
    return json.loads(payload)
