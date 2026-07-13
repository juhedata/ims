#!/bin/bash
# reload_nginx.sh - 平滑重载 Nginx（兼容宝塔面板）
# 用法: ./reload_nginx.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=nginx_common.sh
source "${SCRIPT_DIR}/nginx_common.sh"

echo "🔄 重载 Nginx（${NGINX_BIN}）..."
nginx_reload

echo "✅ Nginx 重载完成"

# 打印当前 Nginx 监听端口，便于排查
echo "📡 当前 Nginx 监听端口:"
if command -v ss &>/dev/null; then
  ss -tlnp | grep nginx || echo "  （未检测到 nginx 监听，请检查配置是否被 include）"
elif command -v netstat &>/dev/null; then
  netstat -tlnp | grep nginx || true
fi
