#!/bin/bash
# verify_deploy.sh - 部署后健康检查
# 用法: ./verify_deploy.sh <前端端口> <后端端口> <静态目录>

set -euo pipefail

APP_PORT="${1:?缺少前端端口}"
BACKEND_PORT="${2:?缺少后端端口}"
BUILD_DIR="${3:?缺少静态目录}"

echo "🔎 部署验证..."

# 1. 静态文件是否存在
if [ ! -f "${BUILD_DIR}/index.html" ]; then
  echo "❌ 静态文件缺失: ${BUILD_DIR}/index.html"
  exit 1
fi
echo "✅ index.html 存在"

# 2. Nginx 是否监听前端端口
if command -v ss &>/dev/null; then
  if ! ss -tln | grep -q ":${APP_PORT} "; then
    echo "❌ Nginx 未监听端口 ${APP_PORT}"
    echo "   请检查: ls /www/server/panel/vhost/nginx/"
    echo "   并确认主配置包含: include /www/server/panel/vhost/nginx/*.conf;"
    ss -tlnp | grep nginx || true
    exit 1
  fi
fi
echo "✅ 端口 ${APP_PORT} 已监听"

# 3. 前端页面可访问
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/" || echo "000")
if [ "${HTTP_CODE}" != "200" ]; then
  echo "❌ 前端页面访问失败，HTTP ${HTTP_CODE}"
  exit 1
fi
echo "✅ 前端页面正常 (HTTP ${HTTP_CODE})"

# 4. API 代理可访问（后端需在 ${BACKEND_PORT} 运行）
HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/health" || echo "000")
if [ "${HEALTH_CODE}" != "200" ]; then
  echo "❌ API 代理失败，HTTP ${HEALTH_CODE}（请确认后端运行在 ${BACKEND_PORT}）"
  curl -v "http://127.0.0.1:${BACKEND_PORT}/health" 2>&1 | tail -5 || true
  exit 1
fi
echo "✅ API 代理正常 (HTTP ${HEALTH_CODE})"

echo "🏁 部署验证通过"
