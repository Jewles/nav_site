#!/bin/bash
# SSL 证书到期检查脚本
# 用法：
#   ./ssl_check.sh                  # 交互式输入
#   ./ssl_check.sh 121.40.97.229 fabu.go2.cn
#   ./ssl_check.sh -f domains.txt   # 批量从文件读

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

check_one() {
    local ip="$1"
    local domain="$2"

    local cert_info
    cert_info=$(echo | openssl s_client -servername "$domain" -connect "${ip}:443" -showcerts 2>/dev/null | openssl x509 -noout -dates -subject -issuer 2>/dev/null) || {
        echo -e "${RED}[失败]${NC} $domain ($ip) — 连接失败或证书不可用"
        return 1
    }

    local not_before not_after
    not_before=$(echo "$cert_info" | grep 'notBefore=' | cut -d= -f2)
    not_after=$(echo "$cert_info" | grep 'notAfter=' | cut -d= -f2)
    local subject issuer
    subject=$(echo "$cert_info" | grep 'subject=' | cut -d= -f2-)
    issuer=$(echo "$cert_info" | grep 'issuer=' | cut -d= -f2-)

    local expire_epoch now_epoch
    expire_epoch=$(date -j -f "%b %d %T %Y %Z" "$not_after" +%s 2>/dev/null) || {
        echo -e "${RED}[失败]${NC} $domain ($ip) — 日期解析失败 (TZ 问题)"
        return 1
    }
    now_epoch=$(date +%s)
    local remaining_days=$(( (expire_epoch - now_epoch) / 86400 ))

    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e " 域名：   ${YELLOW}$domain${NC}"
    echo -e " IP：     $ip"
    echo -e " 主题：   $subject"
    echo -e " 签发者： $issuer"
    echo -e " 开始：   $not_before"
    echo -e " 到期：   $not_after"

    if [ "$remaining_days" -le 0 ]; then
        echo -e " 状态：   ${RED}❌ 已过期 ${remaining_days} 天${NC}"
    elif [ "$remaining_days" -le 7 ]; then
        echo -e " 状态：   ${RED}⚠️  仅剩 ${remaining_days} 天${NC}"
    elif [ "$remaining_days" -le 30 ]; then
        echo -e " 状态：   ${YELLOW}⚠️  剩余 ${remaining_days} 天${NC}"
    else
        echo -e " 状态：   ${GREEN}✅ 剩余 ${remaining_days} 天${NC}"
    fi
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
}

# ── 批量模式 ──
if [ "${1:-}" = "-f" ] && [ -n "${2:-}" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line// /}"
        [ -z "$line" ] || [ "${line:0:1}" = "#" ] && continue
        ip=$(echo "$line" | awk -F'[[:space:],|]+' '{print $1}')
        domain=$(echo "$line" | awk -F'[[:space:],|]+' '{print $2}')
        [ -z "$ip" ] || [ -z "$domain" ] && continue
        check_one "$ip" "$domain"
    done < "$2"
    exit 0
fi

# ── 命令行参数模式 ──
if [ $# -ge 2 ] && [ -n "$1" ] && [ "$1" != "-f" ]; then
    check_one "$1" "$2"
    exit 0
fi

# ── 交互模式 ──
read -p "IP 地址: " ip
read -p "域名 (SNI): " domain
check_one "$ip" "$domain"