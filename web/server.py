#!/usr/bin/env python3
"""Browser UI for Agent Process Monitor."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
AGENT_RUN_PATH = PLUGIN_ROOT / "scripts" / "agent-run.py"

spec = importlib.util.spec_from_file_location("agent_run", AGENT_RUN_PATH)
agent_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(agent_run)

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


def display_path(value: str | None) -> str | None:
    if not value:
        return value
    home = str(Path.home())
    if value == home:
        return "~"
    if value.startswith(home + "\\") or value.startswith(home + "/"):
        value = "~" + value[len(home):]
    return value.replace(home + "\\", "~\\").replace(home + "/", "~/")


def row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    data.pop("command_json", None)
    for key in ("cwd", "stdout_log", "stderr_log"):
        data[key] = display_path(data.get(key))
    data["command_display"] = display_path(data.get("command_display"))
    data["short_id"] = data["id"][:8]
    return data


def get_runs(status: str | None, limit: int) -> list[dict]:
    agent_run.update_running_statuses()
    with agent_run.connect() as db:
        if status:
            rows = db.execute(
                "SELECT * FROM runs WHERE status = ? ORDER BY started_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [row_to_dict(row) for row in rows]


def get_run(run_id: str) -> dict | None:
    agent_run.update_running_statuses()
    with agent_run.connect() as db:
        row = db.execute(
            "SELECT * FROM runs WHERE id LIKE ? ORDER BY started_at DESC LIMIT 1",
            (run_id + "%",),
        ).fetchone()
    return row_to_dict(row) if row else None


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentProcessMonitor/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/runs":
            self.handle_runs(parsed.query)
            return
        if parsed.path.startswith("/api/runs/"):
            self.handle_run_detail(parsed.path)
            return
        self.handle_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/runs/") and parsed.path.endswith("/stop"):
            run_id = parsed.path.split("/")[3]
            args = argparse.Namespace(id=run_id)
            code = agent_run.stop_run(args)
            self.send_json({"ok": code == 0}, HTTPStatus.OK if code == 0 else HTTPStatus.BAD_REQUEST)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_runs(self, query: str) -> None:
        params = parse_qs(query)
        status = params.get("status", [None])[0]
        limit_raw = params.get("limit", ["100"])[0]
        try:
            limit = max(1, min(int(limit_raw), 500))
        except ValueError:
            limit = 100
        self.send_json({"runs": get_runs(status, limit), "database": display_path(str(agent_run.DB_PATH))})

    def handle_run_detail(self, path: str) -> None:
        parts = path.strip("/").split("/")
        if len(parts) < 3:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        run = get_run(parts[2])
        if not run:
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if len(parts) == 4 and parts[3] == "logs":
            stdout = agent_run.redact(agent_run.tail(run.get("stdout_log"), 16000))
            stderr = agent_run.redact(agent_run.tail(run.get("stderr_log"), 16000))
            self.send_json({"run": run, "stdout": stdout, "stderr": stderr})
            return
        self.send_json({"run": run})

    def handle_static(self, path: str) -> None:
        if path in {"/", ""}:
            file_path = STATIC_DIR / "index.html"
        else:
            requested = path.lstrip("/")
            file_path = (STATIC_DIR / requested).resolve()
            if STATIC_DIR.resolve() not in file_path.parents and file_path != STATIC_DIR.resolve():
                self.send_error(HTTPStatus.FORBIDDEN)
                return
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", CONTENT_TYPES.get(file_path.suffix, "application/octet-stream"))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Agent Process Monitor browser UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    agent_run.ensure_storage()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Agent Process Monitor UI: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
