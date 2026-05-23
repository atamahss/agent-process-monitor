# Publishing and Local Setup

## EN

Use `main` as the clean public branch. It must not contain workstation-specific
paths, secrets, local databases, logs, or private runtime configuration.

Keep personal setup outside Git or under ignored paths such as `.local/`.

Before making the repository public or pushing publication changes, run a
pre-publish security pass with at least these stages:

1. Check the current tree for secrets, logs, databases, `.env` files, pycache,
   local usernames, and workstation paths.
2. Check the full Git history and commit metadata for the same data.
3. Check runtime/API/GitHub exposure: repository visibility, remote HEAD, local
   API fields, and network binding behavior.

For local-only experiments, use a branch name such as `local/workstation` and do
not push it.

## RU

Используйте `main` как чистую публичную ветку. В ней не должно быть путей
конкретного ноутбука, секретов, локальных баз данных, логов или приватной
runtime-конфигурации.

Личные настройки держите вне Git или в ignored-папках, например `.local/`.

Перед публикацией репозитория или push изменений для публикации выполняйте
pre-publish security pass минимум в три этапа:

1. Проверить текущее дерево на секреты, логи, базы данных, `.env`, pycache,
   локальные имена пользователей и пути ноутбука.
2. Проверить всю Git history и metadata коммитов на те же данные.
3. Проверить runtime/API/GitHub exposure: видимость репозитория, remote HEAD,
   поля локального API и поведение сетевого bind.

Для локальных экспериментов используйте ветку вида `local/workstation` и не
пушьте ее.
