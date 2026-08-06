#!/usr/bin/env python3
"""
Agent 3: GitHub Publisher Agent - GitHub 仓库发布者
当 Verifier Agent 校验通过后，将 Agent 代码和报告打包发布到 GitHub
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
GITHUB_REPO = "https://github.com/Horacezhang36/Competitive-Analysis.git"

class PublisherAgent:
    """GitHub 仓库发布者"""

    def __init__(self):
        self.name = "publisher"
        self.status = "pending"
        self.max_retries = 3

        # 仓库配置
        self.repo_url = GITHUB_REPO
        self.repo_name = "Competitive-Analysis"

        # 发布检查清单
        self.publish_checklist = {
            "agents_code": PROJECT_ROOT / "agents",
            "reports": PROJECT_ROOT / "reports",
            "readme": PROJECT_ROOT / "README.md",
            "gitignore": PROJECT_ROOT / ".gitignore"
        }

    def run(self, verification_passed: bool = False) -> Dict:
        """执行发布任务"""
        self.status = "preparing"

        if not verification_passed:
            return {
                "status": "failed",
                "error": "Verification not passed. Cannot publish."
            }

        print("[Publisher] Starting GitHub publishing...")

        try:
            # 1. 准备发布文件
            self._prepare_files()

            # 2. 初始化 Git 仓库（如需要）
            self._init_or_update_git()

            # 3. 创建提交
            self._create_commit()

            # 4. 推送到 GitHub
            result = self._push_to_github()

            if result["status"] == "success":
                self.status = "completed"
                print(f"[Publisher] Successfully published to {self.repo_url}")
            else:
                self.status = "failed"

            return result

        except Exception as e:
            print(f"[Publisher] Publishing error: {e}")
            self.status = "failed"
            return {
                "status": "failed",
                "error": str(e)
            }

    def _prepare_files(self):
        """准备要发布的文件"""
        print("[Publisher] Preparing files for publishing...")

        # 确保必要的目录存在
        for name, path in self.publish_checklist.items():
            if path == PROJECT_ROOT / ".gitignore":
                # .gitignore 可能不存在，创建默认的
                if not path.exists():
                    self._create_default_gitignore()
            elif path.is_dir():
                print(f"[Publisher] Directory ready: {path}")

        # 创建 README（如不存在）
        readme_path = PROJECT_ROOT / "README.md"
        if not readme_path.exists():
            self._create_readme()

        print("[Publisher] Files prepared successfully")

    def _create_default_gitignore(self):
        """创建默认的 .gitignore"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# System
.DS_Store
Thumbs.db

# Temporary
*.tmp
.scratchpad.md
"""
        with open(PROJECT_ROOT / ".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("[Publisher] Created .gitignore")

    def _create_readme(self):
        """创建 README 文档"""
        readme_content = f"""# Competitive Analysis Demo

AI 竞品分析报告自动生成项目

## 项目简介

本项目使用 Multi-Agent 系统自动完成 AI 行业竞品分析任务，包括：
- 自动搜索 OpenAI、Claude (Anthropic)、Google AI 的最新产品发布信息
- 生成结构化的 HTML 竞品分析报告
- 校验报告内容准确性
- 自动发布到 GitHub 仓库

## 架构说明

```
agents/
├── generator/     # Agent 1: 报告生成器
├── verifier/     # Agent 2: 内容校验器
├── publisher/    # Agent 3: GitHub 发布器
└── orchestrator/ # Agent 4: 任务编排器
```

## Agent 职责

| Agent | 职责 |
|-------|------|
| Generator | 联网搜索竞品信息，生成 HTML 报告 |
| Verifier | 校验报告内容准确性，决定是否放行 |
| Publisher | 将代码和报告发布到 GitHub |
| Orchestrator | 统筹协调各 Agent 工作流程 |

## 工作流程

1. **Generator** 搜索 OpenAI、Claude、Google 2026 年新品发布
2. **Verifier** 校验报告内容（事实核查、URL验证、完整性检查）
3. 如果校验失败 → 回退到 Generator 重新生成（最多3次）
4. 校验通过后 → **Publisher** 发布到 GitHub

## 技术栈

- Python 3.8+
- Mavis Multi-Agent Framework
- Matrix MCP (联网搜索)

## 使用方法

```bash
# 运行完整流程
python agents/orchestrator/orchestrator_agent.py

# 单独运行各 Agent
python agents/generator/generator_agent.py
python agents/verifier/verifier_agent.py
python agents/publisher/publisher_agent.py
```

## 目录结构

```
Competitive_Analysis_demo/
├── agents/              # Agent 代码目录
│   ├── generator/
│   ├── verifier/
│   ├── publisher/
│   └── orchestrator/
├── reports/             # 生成的报告
├── logs/               # 日志文件
└── README.md           # 本文件
```

## License

MIT License

---

*本项目由 Mavis Multi-Agent Framework 自动生成*
"""
        with open(PROJECT_ROOT / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        print("[Publisher] Created README.md")

    def _init_or_update_git(self):
        """初始化或更新 Git 仓库"""
        print("[Publisher] Checking Git repository...")

        git_dir = PROJECT_ROOT / ".git"

        if not git_dir.exists():
            print("[Publisher] Initializing new Git repository...")
            subprocess.run(
                ["git", "init"],
                cwd=PROJECT_ROOT,
                check=True
            )
            subprocess.run(
                ["git", "remote", "add", "origin", self.repo_url],
                cwd=PROJECT_ROOT,
                check=True
            )
            print("[Publisher] Git repository initialized")
        else:
            print("[Publisher] Git repository already exists")

        # 配置 Git 用户（如需要）
        try:
            subprocess.run(
                ["git", "config", "user.email"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ["git", "config", "user.email", "agent@mavis.ai"],
                cwd=PROJECT_ROOT
            )
            subprocess.run(
                ["git", "config", "user.name", "Mavis Agent"],
                cwd=PROJECT_ROOT
            )

    def _create_commit(self):
        """创建 Git 提交"""
        print("[Publisher] Creating Git commit...")

        # 添加所有文件
        subprocess.run(
            ["git", "add", "-A"],
            cwd=PROJECT_ROOT,
            check=True
        )

        # 检查是否有更改
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():
            print("[Publisher] No changes to commit")
            return

        # 创建提交
        commit_message = f"""Auto-publish: competitive analysis report

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Agents: Generator + Verifier + Publisher + Orchestrator
"""
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=PROJECT_ROOT,
            check=True
        )

        print("[Publisher] Commit created successfully")

    def _push_to_github(self, retry_count: int = 0) -> Dict:
        """推送到 GitHub"""
        print(f"[Publisher] Pushing to GitHub (attempt {retry_count + 1})...")

        try:
            # 尝试推送
            result = subprocess.run(
                ["git", "push", "-u", "origin", "main"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "repo_url": self.repo_url,
                    "message": "Successfully pushed to GitHub"
                }
            else:
                error_msg = result.stderr

                # 检查是否需要认证
                if "Authentication failed" in error_msg or "permission denied" in error_msg.lower():
                    return {
                        "status": "auth_required",
                        "error": "GitHub authentication required. Please provide your GitHub token or login with 'gh auth login'.",
                        "action_required": "auth"
                    }

                raise Exception(error_msg)

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "error": "Push timeout. Network may be slow."
            }

        except Exception as e:
            if retry_count < self.max_retries - 1:
                print(f"[Publisher] Push failed, retrying in 5 seconds...")
                import time
                time.sleep(5)
                return self._push_to_github(retry_count + 1)
            else:
                return {
                    "status": "failed",
                    "error": str(e),
                    "local_commit": "Commit exists locally, but push failed"
                }

    def check_gh_auth(self) -> bool:
        """检查 GitHub CLI 认证状态"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def request_auth(self) -> Dict:
        """请求用户授权"""
        return {
            "status": "auth_required",
            "message": "Please authenticate with GitHub:",
            "options": [
                "1. Run 'gh auth login' in terminal",
                "2. Or provide a GitHub Personal Access Token",
                "3. Token needs 'repo' scope for private repos"
            ]
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Publisher Agent")
    parser.add_argument("--verified", "-v", action="store_true",
                        help="Mark as verified (allow publish)")
    parser.add_argument("--repo", "-r", default=GITHUB_REPO,
                        help="GitHub repository URL")
    args = parser.parse_args()

    agent = PublisherAgent()

    if args.verified:
        result = agent.run(verification_passed=True)
    else:
        result = agent.request_auth()

    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
