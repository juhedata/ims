#!/bin/sh
set -e

echo "等待 MySQL 就绪..."
i=0
until uv run python -c "
from app.db.database import check_db_connection
import sys
sys.exit(0 if check_db_connection() else 1)
" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -ge 60 ]; then
    echo "MySQL 连接超时"
    exit 1
  fi
  sleep 2
done
echo "MySQL 已就绪"

echo "执行数据库迁移..."
uv run alembic upgrade head

echo "初始化管理员账号..."
uv run python scripts/init_admin.py \
  --username "${ADMIN_USERNAME:-admin}" \
  --password "${ADMIN_PASSWORD:-admin123}" \
  --nickname "${ADMIN_NICKNAME:-管理员}"

echo "启动 API 服务..."
exec uv run uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
