---
name: agent-process-monitor
description: Track only processes intentionally launched by the AI agent, requiring a clear goal for each process and storing local run history.
---

# Agent Process Monitor

Use `scripts/agent-run.ps1` or `scripts/agent-run.py` for commands that should appear in the AI-agent process history.

Every tracked launch must include `--goal` describing why the process is being started.

Examples:

```powershell
scripts\agent-run.ps1 run --goal "Check Python launcher" -- python --version
scripts\agent-run.ps1 start --goal "Run local frontend dev server" -- npm run dev
scripts\agent-run.ps1 list
scripts\agent-run.ps1 history
```

The history is stored locally under `%USERPROFILE%\.codex\agent-process-history`.
