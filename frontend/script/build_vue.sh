#!/bin/bash
# build_vue.sh - 构建 Vue 前端并部署静态资源到目标目录
# 用法: ./build_vue.sh <项目源码目录> <部署目标目录>

set -euo pipefail

PROJECT_DIR="$1"
BUILD_DIR="$2"

if [ -z "$PROJECT_DIR" ] || [ -z "$BUILD_DIR" ]; then
  echo "❌ 错误: 缺少必要参数"
  echo "用法: $0 <项目源码目录> <部署目标目录>"
  exit 1
fi

echo "📦 构建 Vue 前端，部署到 ${BUILD_DIR} ..."

WORKDIR=$(mktemp -d)
trap 'rm -rf "${WORKDIR}"' EXIT

# 同步源码到临时目录进行构建
rsync -a \
  --exclude 'node_modules/' \
  --exclude 'dist/' \
  --exclude '.git/' \
  --exclude '.idea/' \
  "${PROJECT_DIR}/" "${WORKDIR}/"

cd "${WORKDIR}"

# 加载 CI config 阶段生成的生产环境变量
if [ -f "${BUILD_DIR}/.env.production" ]; then
  cp "${BUILD_DIR}/.env.production" .env.production
  echo "✅ 已加载生产环境配置: ${BUILD_DIR}/.env.production"
else
  echo "⚠️ 未找到 ${BUILD_DIR}/.env.production，使用默认配置构建"
fi

# ── Node.js 版本检查 & 自动切换 ───────────────────────────────────
REQUIRED_NODE=20
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

# 尝试加载 nvm（GitLab Shell Runner 默认不加载 .bashrc）
if [ -s "${NVM_DIR}/nvm.sh" ]; then
  source "${NVM_DIR}/nvm.sh"
fi

if ! command -v node &>/dev/null; then
  echo "❌ 未找到 Node.js，请先安装 nvm 并运行: nvm install ${REQUIRED_NODE}"
  exit 1
fi

NODE_VER=$(node -e "process.exit(parseInt(process.version.slice(1)))" 2>/dev/null; echo $?)
CURRENT_MAJOR=$(node -e "console.log(parseInt(process.version.slice(1)))")

echo "ℹ️ 当前 Node.js 版本: $(node -v)"

if [ "${CURRENT_MAJOR}" -lt "${REQUIRED_NODE}" ]; then
  echo "⚠️ Node.js 版本过低（当前 ${CURRENT_MAJOR}，需要 ${REQUIRED_NODE}+），尝试用 nvm 切换..."
  if command -v nvm &>/dev/null; then
    # 若已安装对应版本则直接使用，否则自动安装
    nvm install "${REQUIRED_NODE}" --no-progress
    nvm use "${REQUIRED_NODE}"
    echo "✅ 已切换至 Node.js $(node -v)"
  else
    echo "❌ 未找到 nvm，请手动升级 Node.js 到 ${REQUIRED_NODE}+ 后重试"
    echo "   安装 nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash"
    echo "   安装 Node: nvm install ${REQUIRED_NODE} && nvm alias default ${REQUIRED_NODE}"
    exit 1
  fi
fi

echo "✅ Node.js $(node -v) / npm $(npm -v)"

echo "📥 安装依赖（npm ci）..."
npm ci

echo "🔨 执行构建（npm run build）..."
npm run build

if [ ! -d "dist" ]; then
  echo "❌ 构建失败：未生成 dist 目录"
  exit 1
fi

mkdir -p "${BUILD_DIR}"
# 仅部署静态资源，保留 BUILD_DIR 下的 .env.production
rsync -a --delete \
  --exclude '.env.production' \
  dist/ "${BUILD_DIR}/"

echo "✅ 前端构建完成: ${BUILD_DIR}"
ls -alh "${BUILD_DIR}"
