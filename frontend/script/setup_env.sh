#!/bin/bash

# setup_env.sh - 环境配置处理脚本
# 用法: ./setup_env.sh <环境配置模板> <输出配置路径> [环境特定配置]

# 检查必要参数
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "❌ 错误: 缺少必要参数"
  echo "用法: $0 <环境配置模板> <输出配置路径> [环境特定配置]"
  echo "示例: $0 .env.example .env.production .env.dev"
  exit 1
fi

ENV_TEMPLATE="$1"
ENV_OUTPUT="$2"
ENV_SPECIAL="$3"

# 检查模板文件是否存在
if [ ! -f "$ENV_TEMPLATE" ]; then
  echo "❌ 错误: 环境模板文件不存在: $ENV_TEMPLATE"
  exit 1
fi

# 创建输出目录
OUTPUT_DIR=$(dirname "$ENV_OUTPUT")
mkdir -p "$OUTPUT_DIR"

# 复制模板文件
echo "🔧 复制环境配置模板..."
cp "$ENV_TEMPLATE" "$ENV_OUTPUT"

echo "🔧 开始替换 $ENV_OUTPUT 文件里的变量..."

# 查找并替换所有符合 {VARIABLE} 格式的占位符
PLACEHOLDERS=$(grep -o '{[A-Z0-9_]\+}' "$ENV_OUTPUT" | tr -d '{}' | sort | uniq)

if [ -z "$PLACEHOLDERS" ]; then
  echo "ℹ️ 没有找到需要替换的占位符"
else
  for PLACEHOLDER in $PLACEHOLDERS; do
    if [ -z "${!PLACEHOLDER}" ]; then
      echo "⚠️ 警告: 环境变量 $PLACEHOLDER 未定义，保留占位符"
    else
      echo "✅ 替换占位符 {$PLACEHOLDER}"
      sed -i "s|{$PLACEHOLDER}|${!PLACEHOLDER}|g" "$ENV_OUTPUT"
    fi
  done
fi

REMAINING=$(grep -o '{[A-Z0-9_]\+}' "$ENV_OUTPUT" || true)
if [ -n "$REMAINING" ]; then
  echo "⚠️ 警告: 替换后仍有占位符存在:"
  echo "$REMAINING" | tr -d '{}' | sort | uniq | sed 's/^/  - /'
fi

echo "✅ 基本环境变量替换完成。"

# 处理环境特定的配置（如果提供）
if [ -n "$ENV_SPECIAL" ] && [ -f "$ENV_SPECIAL" ]; then
  echo "🔄 从 $ENV_SPECIAL 中读取特定环境变量..."

  while IFS= read -r line || [ -n "$line" ]; do
    if [[ $line =~ ^#.*$ || -z $(echo $line | tr -d '[:space:]') ]]; then
      continue
    fi

    if [[ $line =~ ^([A-Za-z0-9_]+)=(.*)$ ]]; then
      VAR_NAME="${BASH_REMATCH[1]}"
      VAR_VALUE="${BASH_REMATCH[2]}"
      VAR_VALUE=$(echo $VAR_VALUE | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

      echo "✏️ 覆盖变量: $VAR_NAME=$VAR_VALUE"
      if grep -q "^$VAR_NAME=" "$ENV_OUTPUT"; then
        sed -i "s|^$VAR_NAME=.*|$VAR_NAME=$VAR_VALUE|g" "$ENV_OUTPUT"
      else
        echo "$VAR_NAME=$VAR_VALUE" >> "$ENV_OUTPUT"
      fi
    fi
  done < "$ENV_SPECIAL"
  echo "✅ 特定环境变量覆盖完成"
else
  if [ -n "$ENV_SPECIAL" ]; then
    echo "⚠️ 特定环境配置文件不存在: $ENV_SPECIAL，跳过环境特定变量覆盖"
  fi
fi

echo "🏁 环境配置设置完成: $ENV_OUTPUT"
exit 0
