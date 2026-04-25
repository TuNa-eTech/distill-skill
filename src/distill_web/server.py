"""HTTP server for the Distill dashboard API."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .service import (
    DashboardError,
    NotFoundError,
    get_health,
    get_overview,
    get_pipeline,
    get_review_entry,
    list_review_entries,
    list_roles,
)

REVIEW_DETAIL_RE = re.compile(r"^/api/review/(?P<extraction_id>\d+)$")


class ApiRequestError(DashboardError):
    """Raised when the incoming request is invalid."""


class DistillDashboardServer(ThreadingHTTPServer):
    """HTTP server with bound dashboard paths."""

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseHTTPRequestHandler],
        *,
        db_path: Path,
        packs_dir: Path,
    ) -> None:
        super().__init__(server_address, request_handler_class)
        self.db_path = db_path
        self.packs_dir = packs_dir


def _first_query_value(query_params: dict[str, list[str]], key: str, default: str = "") -> str:
    values = query_params.get(key)
    if not values:
        return default
    return values[0]


def _parse_limit(query_params: dict[str, list[str]]) -> int:
    value = _first_query_value(query_params, "limit", "50")
    try:
        return int(value)
    except ValueError as exc:
        raise ApiRequestError("Invalid limit value.") from exc


def _parse_offset(query_params: dict[str, list[str]]) -> int:
    value = _first_query_value(query_params, "offset", "0")
    try:
        return int(value)
    except ValueError as exc:
        raise ApiRequestError("Invalid offset value.") from exc


def _parse_role(query_params: dict[str, list[str]]) -> str:
    return _first_query_value(query_params, "role", "mobile-dev")


class DistillDashboardHandler(BaseHTTPRequestHandler):
    """Serve JSON responses for dashboard routes."""

    server: DistillDashboardServer

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_default_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        query_params = parse_qs(parsed.query)
        try:
            payload = self._route(parsed.path, query_params)
        except NotFoundError as exc:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
            return
        except ApiRequestError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except DashboardError as exc:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
            return
        self._send_json(HTTPStatus.OK, payload)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _route(self, path: str, query_params: dict[str, list[str]]) -> dict[str, Any]:
        if path == "/api/health":
            return get_health(db_path=self.server.db_path, packs_dir=self.server.packs_dir)
        if path == "/api/roles":
            return {
                "roles": list_roles(db_path=self.server.db_path, packs_dir=self.server.packs_dir)
            }
        if path == "/api/overview":
            return get_overview(
                _parse_role(query_params),
                db_path=self.server.db_path,
                packs_dir=self.server.packs_dir,
            )
        if path == "/api/pipeline":
            return get_pipeline(
                _parse_role(query_params),
                db_path=self.server.db_path,
                packs_dir=self.server.packs_dir,
            )
        if path == "/api/review":
            return list_review_entries(
                _parse_role(query_params),
                query=_first_query_value(query_params, "q", ""),
                source=_first_query_value(query_params, "source", "all"),
                cluster=_first_query_value(query_params, "cluster", "all"),
                limit=_parse_limit(query_params),
                offset=_parse_offset(query_params),
                db_path=self.server.db_path,
                packs_dir=self.server.packs_dir,
            )
        match = REVIEW_DETAIL_RE.match(path)
        if match:
            return get_review_entry(
                _parse_role(query_params),
                int(match.group("extraction_id")),
                db_path=self.server.db_path,
                packs_dir=self.server.packs_dir,
            )
        raise NotFoundError(f"Unknown route: {path}")

    def _send_default_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_default_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    db_path: Path | None = None,
    packs_dir: Path | None = None,
) -> DistillDashboardServer:
    from distill_core.config import DB_PATH, PACKS_DIR

    return DistillDashboardServer(
        (host, port),
        DistillDashboardHandler,
        db_path=db_path or DB_PATH,
        packs_dir=packs_dir or PACKS_DIR,
    )


def main() -> None:
    from distill_core.config import DB_PATH, PACKS_DIR

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--packs-dir", type=Path, default=PACKS_DIR)
    args = parser.parse_args()

    server = make_server(
        host=args.host,
        port=args.port,
        db_path=args.db_path,
        packs_dir=args.packs_dir,
    )
    print(
        f"Distill dashboard API serving on http://{args.host}:{args.port} "
        f"(db={args.db_path}, packs={args.packs_dir})"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard API...")
    finally:
        server.server_close()
