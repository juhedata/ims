#!/bin/bash
# setup_nginx.sh - 部署 Nginx 站点配置（自动适配系统/宝塔 Nginx）
# 用法: ./setup_nginx.sh <站点名> <配置文件路径>

set -euo pipefail

SITE_NAME="${1:?❌ 错误: 缺少站点名}"
CONFIG_FILE="${2:?❌ 错误: 缺少配置文件路径}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=nginx_common.sh
source "${SCRIPT_DIR}/nginx_common.sh"

if [ ! -f "${CONFIG_FILE}" ]; then
  echo "❌ 错误: 配置文件不存在: ${CONFIG_FILE}"
  exit 1
fi

mkdir -p "${NGINX_VHOST_DIR}"
mkdir -p /www/wwwlogs

TARGET_FILE="${NGINX_VHOST_DIR}/${SITE_NAME}.conf"

echo "ℹ️ 检测到 Nginx 类型: ${NGINX_TYPE}"
echo "ℹ️ Nginx 二进制: ${NGINX_BIN}"
echo "ℹ️ 站点配置目录: ${NGINX_VHOST_DIR}"
echo "📝 部署 Nginx 配置: ${TARGET_FILE}"

cp -f "${CONFIG_FILE}" "${TARGET_FILE}"

echo "🔍 检查 Nginx 配置..."
nginx_test

echo "✅ Nginx 配置部署完成"
