#!/usr/bin/env python3
"""Track processes intentionally launched by an AI agent.

This launcher records only commands that pass through it. Every launch requires a
human-readable goal so the process history explains why the process exists.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Iterable

APP_DIR = Path(os.environ.get("AGENT_PROCESS_HISTORY_DIR", Path.home() / ".codex" / "agent-process-history"))
DB_PATH = APP_DIR / "history.sqlite"
LOG_DIR = APP_DIR / "logs"

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd|token|api[_-]?key|secret|authorization|bearer)(\s*[=:]\s*)([^\s;&|]+)"),
    re.compile(r"(?i)(bearer\s+)[a-z0-9._~+/=-]{12,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
]

TERMINAL_STATUSES = {"completed", "failed", "stopped_by_agent", "ended_external", "ended_unknown"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def ensure_storage() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                initiated_by TEXT NOT NULL,
                goal TEXT NOT NULL,
                command_display TEXT NOT NULL,
                command_json TEXT NOT NULL,
                cwd TEXT NOT NULL,
                pid INTEGER,
                status TEXT NOT NULL,
                mode TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                exit_code INTEGER,
                stdout_log TEXT,
                stderr_log TEXT,
                notes TEXT
            )
            """
        )
        db.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at)")


def redact(text: str) -> str:
    value = text
    for pattern in SECRET_PATTERNS:
        value = pattern.sub(lambda m: (m.group(1) + m.group(2) + "***") if len(m.groups()) >= 3 else (m.group(1) + "***"), value)
    return value


def redact_argv(command: list[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    for arg in command:
        if redact_next:
            redacted.append("***")
            redact_next = False
            continue

        redacted_arg = redact(arg)
        lower = arg.lower()
        if lower in {"--token", "--password", "--passwd", "--pwd", "--secret", "--api-key", "--apikey", "--authorization"}:
            redact_next = True
        redacted.append(redacted_arg)
    return redacted


def command_to_display(command: list[str], shell: bool) -> str:
    if shell:
        return redact(" ".join(command))
    return redact(subprocess.list2cmdline(redact_argv(command)))


def connect() -> sqlite3.Connection:
    ensure_storage()
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def process_exists(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return str(pid) in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def update_running_statuses() -> None:
    with connect() as db:
        rows = db.execute("SELECT id, pid, status FROM runs WHERE status = 'running'").fetchall()
        for row in rows:
            if not process_exists(row["pid"]):
                db.execute(
                    "UPDATE runs SET status = ?, ended_at = COALESCE(ended_at, ?) WHERE id = ?",
                    ("ended_external", utc_now(), row["id"]),
                )


def insert_run(run: dict) -> None:
    with connect() as db:
        db.execute(
            """
            INSERT INTO runs (
                id, initiated_by, goal, command_display, command_json, cwd, pid,
                status, mode, started_at, ended_at, exit_code, stdout_log, stderr_log, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run["id"], run["initiated_by"], run["goal"], run["command_display"], run["command_json"],
                run["cwd"], run.get("pid"), run["status"], run["mode"], run["started_at"], run.get("ended_at"),
                run.get("exit_code"), run.get("stdout_log"), run.get("stderr_log"), run.get("notes"),
            ),
        )


def update_finished(run_id: str, status: str, exit_code: int | None) -> None:
    with connect() as db:
        db.execute(
            "UPDATE runs SET status = ?, ended_at = ?, exit_code = ? WHERE id = ?",
            (status, utc_now(), exit_code, run_id),
        )


def record_action(args: argparse.Namespace) -> int:
    if not args.goal.strip():
        print("--goal is required and cannot be empty", file=sys.stderr)
        return 2

    ensure_storage()
    run_id = str(uuid.uuid4())
    command = args.command or "manual record"
    cwd = str(Path(args.cwd).resolve()) if args.cwd else os.getcwd()
    now = utc_now()
    run = {
        "id": run_id,
        "initiated_by": "ai_agent",
        "goal": args.goal.strip(),
        "command_display": redact(command),
        "command_json": json.dumps({"recorded": True, "command": redact(command)}, ensure_ascii=False),
        "cwd": cwd,
        "pid": None,
        "status": "recorded",
        "mode": "record",
        "started_at": args.started_at or now,
        "ended_at": args.ended_at or now,
        "exit_code": args.exit_code,
        "stdout_log": None,
        "stderr_log": None,
        "notes": args.notes,
    }
    insert_run(run)
    print(f"id: {run_id}")
    print("status: recorded")
    print(f"goal: {args.goal.strip()}")
    return 0


def build_popen_args(command: list[str], shell: bool) -> tuple[list[str] | str, bool]:
    if shell:
        return " ".join(command), True
    return command, False


def launch(args: argparse.Namespace, wait: bool) -> int:
    if not args.goal.strip():
        print("--goal is required and cannot be empty", file=sys.stderr)
        return 2
    if not args.command:
        print("command is required after --", file=sys.stderr)
        return 2

    ensure_storage()
    run_id = str(uuid.uuid4())
    out_path = LOG_DIR / f"{run_id}.out.log"
    err_path = LOG_DIR / f"{run_id}.err.log"
    cwd = str(Path(args.cwd).resolve()) if args.cwd else os.getcwd()
    command_display = command_to_display(args.command, args.shell)
    popen_command, popen_shell = build_popen_args(args.command, args.shell)

    with out_path.open("ab") as stdout_file, err_path.open("ab") as stderr_file:
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        process = subprocess.Popen(
            popen_command,
            cwd=cwd,
            stdout=stdout_file,
            stderr=stderr_file,
            shell=popen_shell,
            creationflags=creationflags,
        )

    run = {
        "id": run_id,
        "initiated_by": "ai_agent",
        "goal": args.goal.strip(),
        "command_display": command_display,
        "command_json": json.dumps({"argv": redact_argv(args.command), "shell": args.shell}, ensure_ascii=False),
        "cwd": cwd,
        "pid": process.pid,
        "status": "running",
        "mode": "run" if wait else "start",
        "started_at": utc_now(),
        "stdout_log": str(out_path),
        "stderr_log": str(err_path),
        "notes": args.notes,
    }
    insert_run(run)

    print(f"id: {run_id}")
    print(f"pid: {process.pid}")
    print(f"goal: {args.goal.strip()}")
    print(f"status: running")

    if not wait:
        return 0

    try:
        exit_code = process.wait()
    except KeyboardInterrupt:
        stop_process(process.pid)
        update_finished(run_id, "stopped_by_agent", None)
        raise

    update_finished(run_id, "completed" if exit_code == 0 else "failed", exit_code)
    print(f"status: {'completed' if exit_code == 0 else 'failed'}")
    print(f"exit_code: {exit_code}")
    return exit_code


def stop_process(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
    else:
        os.kill(pid, signal.SIGTERM)


def stop_run(args: argparse.Namespace) -> int:
    update_running_statuses()
    with connect() as db:
        row = db.execute("SELECT * FROM runs WHERE id = ?", (args.id,)).fetchone()
        if not row:
            print(f"No run found for id {args.id}", file=sys.stderr)
            return 1
        if row["status"] != "running":
            print(f"Run {args.id} is already {row['status']}")
            return 0
        pid = row["pid"]
        if not process_exists(pid):
            db.execute("UPDATE runs SET status = ?, ended_at = ? WHERE id = ?", ("ended_external", utc_now(), args.id))
            print(f"Run {args.id} is no longer running")
            return 0
        stop_process(pid)
        db.execute("UPDATE runs SET status = ?, ended_at = ? WHERE id = ?", ("stopped_by_agent", utc_now(), args.id))
        print(f"Stopped {args.id} pid {pid}")
        return 0


def format_row(row: sqlite3.Row) -> str:
    ended = row["ended_at"] or "-"
    exit_code = "-" if row["exit_code"] is None else str(row["exit_code"])
    return (
        f"{row['id'][:8]}  {row['status']:<16} pid={str(row['pid'] or '-'):>6} "
        f"exit={exit_code:<4} start={row['started_at']} end={ended}\n"
        f"  goal: {row['goal']}\n"
        f"  cmd : {row['command_display']}\n"
        f"  cwd : {row['cwd']}"
    )


def list_runs(args: argparse.Namespace, running_only: bool) -> int:
    update_running_statuses()
    with connect() as db:
        if running_only:
            rows = db.execute("SELECT * FROM runs WHERE status = 'running' ORDER BY started_at DESC").fetchall()
        else:
            rows = db.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (args.limit,)).fetchall()
    if not rows:
        print("No agent-initiated process records yet.")
        return 0
    for row in rows:
        print(format_row(row))
    return 0


def show_run(args: argparse.Namespace) -> int:
    update_running_statuses()
    with connect() as db:
        row = db.execute("SELECT * FROM runs WHERE id LIKE ? ORDER BY started_at DESC LIMIT 1", (args.id + "%",)).fetchone()
    if not row:
        print(f"No run found for id prefix {args.id}", file=sys.stderr)
        return 1
    print(format_row(row))
    print(f"  stdout: {row['stdout_log'] or '-'}")
    print(f"  stderr: {row['stderr_log'] or '-'}")
    if args.logs:
        print("\n--- stdout tail ---")
        print(tail(row["stdout_log"]))
        print("\n--- stderr tail ---")
        print(tail(row["stderr_log"]))
    return 0


def tail(path_value: str | None, size: int = 4000) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        return ""
    data = path.read_bytes()[-size:]
    return data.decode("utf-8", errors="replace")


def db_info(_: argparse.Namespace) -> int:
    ensure_storage()
    print(f"database: {DB_PATH}")
    print(f"logs: {LOG_DIR}")
    return 0


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track processes intentionally launched by an AI agent.")
    sub = parser.add_subparsers(dest="command_name", required=True)

    def add_launch_parser(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--goal", required=True, help="Required purpose of this agent-initiated process.")
        p.add_argument("--cwd", help="Working directory. Defaults to the current directory.")
        p.add_argument("--notes", help="Optional extra note for the history record.")
        p.add_argument("--shell", action="store_true", help="Run the command through the system shell.")
        p.add_argument("command", nargs=argparse.REMAINDER, help="Command to run, usually after --")
        return p

    add_launch_parser("run", "Run a command, wait for completion, and record the result.")
    add_launch_parser("start", "Start a long-running command and return immediately.")

    p_record = sub.add_parser("record", help="Record an agent action that happened outside this launcher.")
    p_record.add_argument("--goal", required=True, help="Required purpose of the recorded agent action.")
    p_record.add_argument("--command", help="Command or action summary to display.")
    p_record.add_argument("--cwd", help="Working directory. Defaults to the current directory.")
    p_record.add_argument("--notes", help="Optional extra note for the history record.")
    p_record.add_argument("--started-at", help="Optional ISO timestamp for when the action started.")
    p_record.add_argument("--ended-at", help="Optional ISO timestamp for when the action ended.")
    p_record.add_argument("--exit-code", type=int, help="Optional exit code when the action represented a command.")

    p_list = sub.add_parser("list", help="Show currently running agent-initiated processes.")
    p_list.add_argument("--limit", type=int, default=20)

    p_history = sub.add_parser("history", help="Show recent agent-initiated process history.")
    p_history.add_argument("--limit", type=int, default=20)

    p_stop = sub.add_parser("stop", help="Stop a running process by run id.")
    p_stop.add_argument("id")

    p_show = sub.add_parser("show", help="Show one run by id prefix.")
    p_show.add_argument("id")
    p_show.add_argument("--logs", action="store_true")

    sub.add_parser("where", help="Show database and log locations.")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    if args.command_name in {"run", "start"}:
        if args.command and args.command[0] == "--":
            args.command = args.command[1:]
        return launch(args, wait=args.command_name == "run")
    if args.command_name == "record":
        return record_action(args)
    if args.command_name == "list":
        return list_runs(args, running_only=True)
    if args.command_name == "history":
        return list_runs(args, running_only=False)
    if args.command_name == "stop":
        return stop_run(args)
    if args.command_name == "show":
        return show_run(args)
    if args.command_name == "where":
        return db_info(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
