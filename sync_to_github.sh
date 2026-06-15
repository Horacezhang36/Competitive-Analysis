#!/bin/bash
# GitHub 持续更新同步脚本
# 用法: ./sync_to_github.sh [commit message]

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

COMMIT_MSG="${1:-Auto sync: $(date '+%Y-%m-%d %H:%M:%S')}"

echo "📂 仓库目录: $REPO_DIR"
echo "📝 提交信息: $COMMIT_MSG"
echo ""

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "⚠️  没有检测到变更，跳过提交。"
    exit 0
fi

# 添加所有变更
git add -A

# 提交
git commit -m "$COMMIT_MSG"

# 推送
git push origin main

echo ""
echo "✅ 同步完成！"
