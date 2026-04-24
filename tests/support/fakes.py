from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self._payload


@dataclass
class FakeSession:
    responses: dict[str, list[FakeResponse] | FakeResponse]
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def get(
        self,
        url: str,
        *,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        auth: Any = None,
        timeout: int | None = None,
    ) -> FakeResponse:
        self.calls.append(
            (
                url,
                {
                    "headers": headers or {},
                    "params": params or {},
                    "auth": auth,
                    "timeout": timeout,
                },
            )
        )
        for key, response in self.responses.items():
            if url.endswith(key):
                if isinstance(response, list):
                    if not response:
                        raise AssertionError(f"No more fake responses for {key}")
                    return response.pop(0)
                return response
        raise AssertionError(f"Unexpected URL: {url}")
