#!/bin/bash
# nginx_common.sh - 自动检测实际运行的 Nginx（系统 / 宝塔）

detect_nginx() {
  # 优先：系统 Nginx（/etc/nginx/nginx.conf 存在且可用）
  if [ -f /etc/nginx/nginx.conf ]; then
    local SYS_NGINX
    SYS_NGINX=$(command -v nginx 2>/dev/null || echo /usr/sbin/nginx)
    if [ -x "${SYS_NGINX}" ] && "${SYS_NGINX}" -t 2>/dev/null; then
      NGINX_BIN="${SYS_NGINX}"
      NGINX_CONF=/etc/nginx/nginx.conf
      NGINX_VHOST_DIR=/etc/nginx/conf.d
      NGINX_TYPE="system"
      return 0
    fi
  fi

  # 其次：完整安装的宝塔 Nginx
  if [ -x /www/server/nginx/sbin/nginx ] && [ -f /www/server/nginx/conf/nginx.conf ]; then
    NGINX_BIN=/www/server/nginx/sbin/nginx
    NGINX_CONF=/www/server/nginx/conf/nginx.conf
    NGINX_VHOST_DIR=/www/server/panel/vhost/nginx
    NGINX_TYPE="bt"
    return 0
  fi

  # 兜底：仅有宝塔二进制但主配置缺失时，仍用系统 conf.d
  if command -v nginx &>/dev/null && [ -d /etc/nginx/conf.d ]; then
    NGINX_BIN=$(command -v nginx)
    NGINX_CONF=/etc/nginx/nginx.conf
    NGINX_VHOST_DIR=/etc/nginx/conf.d
    NGINX_TYPE="system-fallback"
    return 0
  fi

  echo "❌ 未找到可用的 Nginx"
  return 1
}

detect_nginx || exit 1

nginx_test() {
  "${NGINX_BIN}" -t
}

nginx_reload() {
  nginx_test
  if systemctl is-active nginx &>/dev/null; then
    systemctl reload nginx
  elif [ -x /etc/init.d/nginx ]; then
    /etc/init.d/nginx reload
  else
    "${NGINX_BIN}" -s reload
  fi
}
