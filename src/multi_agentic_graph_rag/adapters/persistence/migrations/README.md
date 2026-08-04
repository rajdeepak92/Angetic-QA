# PostgreSQL migrations

Migrations are immutable UTF-8 SQL files named with a four-digit increasing version. The PostgreSQL
adapter applies them transactionally under an advisory lock and records each exact SHA-256 checksum
in `agentic_qa.schema_migrations`. Destructive rollback is intentionally unsupported; use the
explicitly confirmed project-volume reset for disposable local data.
