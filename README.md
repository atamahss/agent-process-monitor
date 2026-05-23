# Agent Process Monitor

## Description / Описание

**EN:** Agent Process Monitor tracks only processes intentionally launched by an
AI agent. Every tracked launch requires a clear goal, so the local history shows
what was started, why it was started, when it finished, and where to inspect its
logs.

**RU:** Agent Process Monitor отслеживает только процессы, которые ИИ-агент
запустил намеренно. Для каждого запуска обязательна понятная цель, поэтому в
локальной истории видно, что было запущено, зачем, когда завершилось и где
посмотреть логи.

## Overview / Обзор

**EN:** Agent Process Monitor is a local Codex plugin and launcher for tracking
only the processes intentionally started by an AI agent.

**RU:** Agent Process Monitor - это локальный плагин Codex и launcher для учета
только тех процессов, которые ИИ-агент запустил намеренно.

**EN:** Each tracked process requires a human-readable goal, so the history
answers:

**RU:** Для каждого отслеживаемого процесса обязательна понятная человеку цель,
поэтому история отвечает на вопросы:

- **EN:** what was started;
  **RU:** что было запущено;
- **EN:** why it was started;
  **RU:** зачем это было запущено;
- **EN:** when it started and ended;
  **RU:** когда процесс стартовал и завершился;
- **EN:** which PID and exit code were observed;
  **RU:** какой PID и exit code были зафиксированы;
- **EN:** where stdout and stderr logs were written.
  **RU:** где лежат stdout и stderr логи.

**EN:** The project includes a small browser UI at `http://127.0.0.1:8765/`
with:

**RU:** В проект входит небольшой браузерный интерфейс на
`http://127.0.0.1:8765/` с возможностями:

- **EN:** Running and History tabs;
  **RU:** вкладки "Сейчас" и "История";
- **EN:** RU/EN language switch;
  **RU:** переключатель языков RU/EN;
- **EN:** search and status filtering;
  **RU:** поиск и фильтрация по статусам;
- **EN:** process details and log tails;
  **RU:** детали процесса и хвосты логов;
- **EN:** low-cost auto-refresh every 10 seconds while the tab is visible.
  **RU:** легкое автообновление раз в 10 секунд, только пока вкладка видима.

## Why / Зачем

**EN:** AI coding agents often start local servers, tests, converters, MCP
helpers, and other long-running processes. Once a chat is stopped or restarted,
it can be hard to know which process is still alive and why it was launched.

**RU:** ИИ-агенты для разработки часто запускают локальные серверы, тесты,
конвертеры, MCP-помощники и другие долгоживущие процессы. После остановки или
перезапуска чата бывает трудно понять, какой процесс еще жив и зачем он был
запущен.

**EN:** This tool keeps an explicit, local audit trail for agent-initiated
processes without monitoring the whole operating system.

**RU:** Этот инструмент ведет явный локальный журнал процессов, инициированных
агентом, не наблюдая за всей операционной системой.

## Commands / Команды

**EN:** Use `agent-run` for commands that should be visible in the process
history.

**RU:** Используйте `agent-run` для команд, которые должны быть видны в истории
процессов.

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

**EN:** `run` waits for completion and records the exit code.

**RU:** `run` ждет завершения команды и записывает exit code.

**EN:** `start` returns immediately and keeps the process in `running` until a
later `list`/`history`/`show` notices that the PID ended or until `stop` is used.

**RU:** `start` сразу возвращает управление и оставляет процесс в статусе
`running`, пока последующий `list`/`history`/`show` не заметит, что PID исчез,
или пока не будет использована команда `stop`.

**EN:** `record` adds an explicit history entry for an agent action that already
happened outside the launcher.

**RU:** `record` добавляет явную запись в историю для действия агента, которое
уже произошло вне launcher.

## Browser UI / Браузерный интерфейс

**EN:** Start the UI through the launcher so the UI itself is tracked:

**RU:** Запускайте UI через launcher, чтобы сам UI тоже был записан в историю:

```powershell
python scripts\agent-run.py start --goal "Show AI-agent process history in browser" -- python web\server.py --port 8765
```

**EN:** Then open:

**RU:** Затем откройте:

```text
http://127.0.0.1:8765/
```

**EN:** The UI is intentionally dependency-light: plain Python standard library
plus HTML, CSS, and JavaScript.

**RU:** UI специально сделан без тяжелых зависимостей: стандартная библиотека
Python плюс обычные HTML, CSS и JavaScript.

## Storage / Хранилище

**EN:** Database and logs are stored outside project folders by default:

**RU:** По умолчанию база данных и логи хранятся вне проектных папок:

```text
C:\Users\<you>\.codex\agent-process-history
```

**EN:** You can override the storage folder with:

**RU:** Папку хранения можно переопределить так:

```powershell
$env:AGENT_PROCESS_HISTORY_DIR = "C:\path\to\history"
```

## Privacy / Приватность

**EN:** The launcher masks common token/password/API-key patterns before storing
command text. It only records commands launched through `agent-run`; it does not
watch all system processes.

**RU:** Launcher маскирует распространенные шаблоны токенов, паролей и API-ключей
перед сохранением текста команды. Он записывает только команды, запущенные через
`agent-run`, и не следит за всеми системными процессами.

## Microsoft Defender note / Примечание про Microsoft Defender

**EN:** Avoid installing or updating this plugin through long pasted PowerShell
commands. Defender can classify that pattern as ClickFix-like behavior because
it resembles instructions that create scripts from copied terminal text.

**RU:** Не устанавливайте и не обновляйте этот плагин через длинные вставленные
PowerShell-команды. Defender может классифицировать такой паттерн как похожий на
ClickFix, потому что он напоминает инструкции, создающие скрипты из текста,
скопированного в терминал.

**EN:** Prefer normal files in this plugin folder and short commands that run
those files.

**RU:** Лучше использовать обычные файлы в папке плагина и короткие команды,
которые запускают эти файлы.
