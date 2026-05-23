# Agent Process Monitor

Agent Process Monitor is a local Codex plugin and launcher for tracking only the
processes intentionally started by an AI agent.

Each tracked process requires a human-readable goal, so the history answers:

- what was started;
- why it was started;
- when it started and ended;
- which PID and exit code were observed;
- where stdout and stderr logs were written.

The project includes a small browser UI at `http://127.0.0.1:8765/` with:

- Running and History tabs;
- RU/EN language switch;
- search and status filtering;
- process details and log tails;
- low-cost auto-refresh every 10 seconds while the tab is visible.

## Why

AI coding agents often start local servers, tests, converters, MCP helpers, and
other long-running processes. Once a chat is stopped or restarted, it can be hard
to know which process is still alive and why it was launched.

This tool keeps an explicit, local audit trail for agent-initiated processes
without monitoring the whole operating system.

## Commands

```powershell
scripts\agent-run.ps1 run --goal "Check Python launcher" -- python --version
scripts\agent-run.ps1 start --goal "Run local dev server" -- npm run dev
scripts\agent-run.ps1 list
scripts\agent-run.ps1 history
scripts\agent-run.ps1 show <id> --logs
scripts\agent-run.ps1 stop <id>
scripts\agent-run.ps1 where
scripts\agent-run.ps1 record --goal "Prepared GitHub repository" --command "git init; git commit"
```

`run` waits for completion and records the exit code. `start` returns
immediately and keeps the process in `running` until a later
`list`/`history`/`show` notices that the PID ended or until `stop` is used.
`record` adds an explicit history entry for an agent action that already
happened outside the launcher.

## Browser UI

Start the UI through the launcher so the UI itself is tracked:

```powershell
python scripts\agent-run.py start --goal "Show AI-agent process history in browser" -- python web\server.py --port 8765
```

Then open:

```text
http://127.0.0.1:8765/
```

The UI is intentionally dependency-light: plain Python standard library plus
HTML, CSS, and JavaScript.

## Storage

Database and logs are stored outside project folders by default:

```text
C:\Users\<you>\.codex\agent-process-history
```

You can override the storage folder with:

```powershell
$env:AGENT_PROCESS_HISTORY_DIR = "C:\path\to\history"
```

## Privacy

The launcher masks common token/password/API-key patterns before storing command
text. It only records commands launched through `agent-run`; it does not watch
all system processes.

## Microsoft Defender note

Avoid installing or updating this plugin through long pasted PowerShell
commands. Defender can classify that pattern as ClickFix-like behavior because
it resembles instructions that create scripts from copied terminal text.

Prefer normal files in this plugin folder and short commands that run those
files.
