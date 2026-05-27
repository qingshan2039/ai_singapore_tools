#!/bin/sh
set -e

# 首次启动：如果 SQLite 文件不存在，用 sql/schema.sql 初始化
DB_PATH="${DB_PATH:-/data/toto.db}"
if [ ! -f "$DB_PATH" ]; then
    echo "[entrypoint] initializing SQLite at $DB_PATH"
    mkdir -p "$(dirname "$DB_PATH")"
    sqlite3 "$DB_PATH" < /app/sql/schema.sql
fi

# 已存在的库：补跑一次 schema（CREATE TABLE IF NOT EXISTS，幂等，不会清数据）
# 如果以后加了 ALTER 列，请在这里追加 ALTER ... IF NOT EXISTS 风格的迁移
sqlite3 "$DB_PATH" < /app/sql/schema.sql || true

exec "$@"
