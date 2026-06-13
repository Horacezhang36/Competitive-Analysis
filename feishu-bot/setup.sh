#!/usr/bin/env bash
set -e

# ═══════════════════════════════════════════════════════════
#  飞书 AI 机器人一键配置脚本
#  扫码即用，3 分钟激活
# ═══════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════╗"
echo "  ║       🦜 飞书 AI 助手 · 一键激活         ║"
echo "  ╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: 检查依赖 ──────────────────────────────────
echo -e "\n${BOLD}[1/4]${NC} 检查 Python 环境..."
python3 --version || { echo -e "${RED}❌ 需要 Python 3.10+${NC}"; exit 1; }
echo -e "${GREEN}✅ Python 就绪${NC}"

# ── Step 2: 安装依赖 ──────────────────────────────────
echo -e "\n${BOLD}[2/4]${NC} 安装 Python 依赖..."
pip3 install -r requirements.txt -q
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# ── Step 3: 配置 .env ──────────────────────────────────
echo -e "\n${BOLD}[3/4]${NC} 配置凭据..."

if [ ! -f .env ]; then
    cp .env.example .env
fi

# 飞书 App ID
read -p "  飞书 App ID (cli_xxx): " APP_ID
if [ -n "$APP_ID" ]; then
    sed -i "s/^FEISHU_APP_ID=.*/FEISHU_APP_ID=$APP_ID/" .env
fi

# 飞书 App Secret
read -p "  飞书 App Secret: " APP_SECRET
if [ -n "$APP_SECRET" ]; then
    sed -i "s/^FEISHU_APP_SECRET=.*/FEISHU_APP_SECRET=$APP_SECRET/" .env
fi

# 飞书 Verify Token
read -p "  飞书 Verify Token: " VERIFY_TOKEN
if [ -n "$VERIFY_TOKEN" ]; then
    sed -i "s/^FEISHU_VERIFY_TOKEN=.*/FEISHU_VERIFY_TOKEN=$VERIFY_TOKEN/" .env
fi

# OpenAI Key
read -p "  OpenAI API Key (sk-xxx): " OAI_KEY
if [ -n "$OAI_KEY" ]; then
    sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$OAI_KEY/" .env
fi

echo -e "${GREEN}✅ 配置已保存到 .env${NC}"

# ── Step 4: 启动 ──────────────────────────────────────
echo -e "\n${BOLD}[4/4]${NC} 启动服务..."

# 检查是否有公网地址（ngrok 或已有域名）
PUBLIC_URL="${PUBLIC_URL:-}"

if [ -z "$PUBLIC_URL" ]; then
    echo -e "\n${YELLOW}⚠️  需要公网地址让飞书能回调你的服务${NC}"
    echo ""
    echo -e "  选择一个方式暴露公网地址："
    echo -e "  ${CYAN}1)${NC} 使用 ngrok (免费):  ngrok http 8080"
    echo -e "  ${CYAN}2)${NC} 部署到云服务器 (推荐)"
    echo -e "  ${CYAN}3)${NC} 使用 Cloudflare Tunnel"
    echo ""
    echo -e "  ${BOLD}最简单的方式：新开一个终端运行${NC}"
    echo -e "  ${GREEN}  ngrok http 8080${NC}"
    echo -e "  然后把 ngrok 提供的 https 地址填到飞书后台"
    echo ""

    # 尝试自动启动 ngrok
    if command -v ngrok &> /dev/null; then
        echo -e "${GREEN}检测到 ngrok，自动启动...${NC}"
        ngrok http 8080 &
        sleep 3
    fi
fi

echo -e "\n${GREEN}${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  🚀 启动飞书机器人...${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}接下来你需要：${NC}"
echo -e "  ${CYAN}1)${NC} 去飞书开放平台配置事件回调地址"
echo -e "     回调地址: ${YELLOW}https://你的域名/feishu/event${NC}"
echo -e "  ${CYAN}2)${NC} 在飞书中搜索你的机器人名称并对话"
echo -e "  ${CYAN}3)${NC} 搞定！🎉"
echo ""

python3 bot.py
