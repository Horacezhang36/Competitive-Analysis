#!/bin/bash
# Competitive Analysis Demo - 快速启动脚本
# 使用方法: ./run.sh 或 bash run.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🎯 Competitive Analysis Demo${NC}"
echo -e "${BLUE}   竞品分析 Multi-Agent 系统${NC}"
echo -e "${BLUE}========================================${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo -e "\n${YELLOW}项目路径: $PROJECT_ROOT${NC}\n"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 需要 Python 3${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 检测通过"

# 检查必要目录
mkdir -p "$PROJECT_ROOT/reports"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/agents/generator"
mkdir -p "$PROJECT_ROOT/agents/verifier"
mkdir -p "$PROJECT_ROOT/agents/publisher"
mkdir -p "$PROJECT_ROOT/agents/orchestrator"

echo -e "${GREEN}✓${NC} 目录结构检查完成"

# 主菜单
show_menu() {
    echo -e "\n${BLUE}请选择操作:${NC}"
    echo "1. 🚀 启动完整工作流 (Generator → Verifier → Publisher)"
    echo "2. 📊 只运行 Generator (生成报告)"
    echo "3. 🔍 只运行 Verifier (校验报告)"
    echo "4. 📤 只运行 Publisher (发布到 GitHub)"
    echo "5. 🧪 单独测试所有 Agent"
    echo "0. ❌ 退出"
    echo ""
    read -p "请输入选项 [0-5]: " choice
}

# 运行选项
run_workflow() {
    echo -e "\n${GREEN}🚀 启动完整工作流...${NC}"
    cd "$PROJECT_ROOT"
    python3 agents/orchestrator/orchestrator_agent.py
}

run_generator() {
    echo -e "\n${GREEN}📊 运行 Generator Agent...${NC}"
    cd "$PROJECT_ROOT"
    python3 agents/generator/generator_agent.py
}

run_verifier() {
    echo -e "\n${GREEN}🔍 运行 Verifier Agent...${NC}"
    cd "$PROJECT_ROOT"
    python3 agents/verifier/verifier_agent.py --report "$PROJECT_ROOT/reports/competitive_analysis_report.html"
}

run_publisher() {
    echo -e "\n${GREEN}📤 运行 Publisher Agent...${NC}"
    cd "$PROJECT_ROOT"
    python3 agents/publisher/publisher_agent.py --verified
}

test_agents() {
    echo -e "\n${GREEN}🧪 测试所有 Agent...${NC}"
    echo ""

    echo -e "${YELLOW}--- 测试 Generator ---${NC}"
    run_generator

    echo -e "\n${YELLOW}--- 测试 Verifier ---${NC}"
    run_verifier

    echo -e "\n${YELLOW}--- 测试 Publisher ---${NC}"
    read -p "是否发布到 GitHub? (需要验证通过) [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        run_publisher
    fi
}

# 主循环
while true; do
    show_menu

    case $choice in
        1)
            run_workflow
            ;;
        2)
            run_generator
            ;;
        3)
            run_verifier
            ;;
        4)
            run_publisher
            ;;
        5)
            test_agents
            ;;
        0)
            echo -e "\n${GREEN}再见! 👋${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}无效选项，请重新输入${NC}"
            ;;
    esac

    echo ""
    read -p "按 Enter 键继续..." anykey
done