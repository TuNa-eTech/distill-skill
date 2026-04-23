import json
import re
from typing import Any

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import env, llm_model


def client() -> Anthropic:
    return Anthropic(api_key=env("ANTHROPIC_API_KEY", required=True))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
def complete(
    *,
    system: str,
    user: str,
    max_tokens: int = 2000,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    resp = client().messages.create(
        model=model or llm_model(),
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> Any:
    match = _JSON_FENCE.search(text)
    payload = match.group(1) if match else text
    return json.loads(payload)
