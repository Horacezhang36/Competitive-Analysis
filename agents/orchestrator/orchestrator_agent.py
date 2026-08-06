#!/usr/bin/env python3
"""
Agent 4: Orchestrator Agent - 任务编排器 / Agent 项目经理
作为 Agent 团队的大脑，统筹协调 Generator、Verifier、Publisher 三个 Agent 的工作流程
处理 Agent 间通信、状态管理和错误恢复
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

class AgentStatus(Enum):
    """Agent 状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PASSED = "passed"
    NEEDS_REVISION = "needs_revision"

@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_id: str
    started_at: str
    current_step: str = "initial"
    generator_status: str = "pending"
    verifier_status: str = "pending"
    publisher_status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3
    report_path: str = "reports/competitive_analysis_report.html"
    verification_report_path: str = "logs/verification_report.md"
    final_status: Optional[str] = None
    error_message: Optional[str] = None

class OrchestratorAgent:
    """任务编排器 Agent"""

    def __init__(self):
        self.name = "orchestrator"
        self.agents = {
            "generator": PROJECT_ROOT / "agents/generator/generator_agent.py",
            "verifier": PROJECT_ROOT / "agents/verifier/verifier_agent.py",
            "publisher": PROJECT_ROOT / "agents/publisher/publisher_agent.py"
        }

        self.state_file = LOGS_DIR / "workflow_state.json"
        self.log_file = LOGS_DIR / "orchestrator.log"

    def run(self) -> Dict:
        """执行完整的工作流程"""
        print("=" * 60)
        print("🎯 Orchestrator Agent - 任务编排器启动")
        print("=" * 60)

        # 初始化工作流状态
        state = self._init_workflow()

        try:
            # === STEP 1: 触发 Generator ===
            print("\n📊 STEP 1: 触发报告生成器 (Generator)")
            state.current_step = "generator"
            state.generator_status = "running"

            generator_result = self._run_generator(state)

            if generator_result["status"] == "failed":
                state.generator_status = "failed"
                state.final_status = "failed"
                state.error_message = f"Generator failed: {generator_result.get('error')}"
                self._save_state(state)
                return self._finalize(state)

            state.generator_status = "completed"
            self._save_state(state)

            # === STEP 2: 触发 Verifier ===
            print("\n🔍 STEP 2: 触发内容校验器 (Verifier)")
            state.current_step = "verifier"
            state.verifier_status = "running"

            verifier_result = self._run_verifier(state)

            if verifier_result["status"] == "failed":
                state.verifier_status = "failed"
                print("\n⚠️ Verifier 检测到问题，需要回退到 Generator 重新生成...")

                # 回退循环（最多3次）
                while state.retry_count < state.max_retries:
                    state.retry_count += 1
                    print(f"\n🔄 回退循环 #{state.retry_count}/{state.max_retries}")

                    print(f"\n📊 STEP 1.{state.retry_count}: 重新触发 Generator")
                    state.current_step = f"generator_retry_{state.retry_count}"
                    state.generator_status = "running"

                    retry_result = self._run_generator(state)

                    if retry_result["status"] == "failed":
                        state.generator_status = "failed"
                        continue

                    state.generator_status = "completed"

                    print(f"\n🔍 STEP 2.{state.retry_count}: 重新校验")
                    state.current_step = f"verifier_retry_{state.retry_count}"
                    state.verifier_status = "running"

                    verifier_result = self._run_verifier(state)

                    if verifier_result["status"] == "passed":
                        state.verifier_status = "passed"
                        break

                if state.retry_count >= state.max_retries and verifier_result["status"] != "passed":
                    state.verifier_status = "failed"
                    state.final_status = "failed"
                    state.error_message = f"Max retries ({state.max_retries}) exceeded. Verification failed."
                    self._save_state(state)
                    return self._finalize(state)
            else:
                state.verifier_status = "passed"

            self._save_state(state)

            # === STEP 3: 触发 Publisher ===
            print("\n🚀 STEP 3: 触发 GitHub 发布器 (Publisher)")
            state.current_step = "publisher"
            state.publisher_status = "running"

            publisher_result = self._run_publisher(state)

            if publisher_result["status"] == "success":
                state.publisher_status = "completed"
                state.final_status = "success"
                print("\n✅ 所有步骤完成！")
            else:
                state.publisher_status = "failed"
                state.final_status = "partial_success"
                state.error_message = f"Publisher failed: {publisher_result.get('error')}"
                print("\n⚠️ 发布部分失败，请检查错误信息")

            self._save_state(state)
            return self._finalize(state)

        except Exception as e:
            print(f"\n❌ 工作流执行异常: {e}")
            state.final_status = "error"
            state.error_message = str(e)
            self._save_state(state)
            return {
                "status": "error",
                "error": str(e),
                "state": self._state_to_dict(state)
            }

    def _init_workflow(self) -> WorkflowState:
        """初始化工作流状态"""
        import uuid
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        state = WorkflowState(
            workflow_id=str(uuid.uuid4())[:8],
            started_at=datetime.now().isoformat()
        )

        print(f"工作流 ID: {state.workflow_id}")
        print(f"开始时间: {state.started_at}")

        self._save_state(state)
        return state

    def _run_generator(self, state: WorkflowState) -> Dict:
        """运行 Generator Agent"""
        print(f"执行 Generator: {self.agents['generator']}")

        try:
            result = subprocess.run(
                [sys.executable, str(self.agents["generator"])],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return self._parse_agent_result(result.stdout, default_status="completed")
            else:
                return {
                    "status": "failed",
                    "error": result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "error": "Generator timeout"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def _run_verifier(self, state: WorkflowState) -> Dict:
        """运行 Verifier Agent"""
        print(f"执行 Verifier: {self.agents['verifier']}")

        try:
            result = subprocess.run(
                [sys.executable, str(self.agents["verifier"]),
                 "--report", str(state.report_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=180
            )

            if result.returncode == 0:
                return self._parse_agent_result(result.stdout, default_status="completed")
            else:
                parsed = self._parse_agent_result(result.stdout, default_status="failed")
                if parsed.get("status") != "failed" or parsed.get("error"):
                    return parsed
                return {
                    "status": "failed",
                    "error": result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "error": "Verifier timeout"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def _run_publisher(self, state: WorkflowState) -> Dict:
        """运行 Publisher Agent"""
        print(f"执行 Publisher: {self.agents['publisher']}")

        try:
            result = subprocess.run(
                [sys.executable, str(self.agents["publisher"]),
                 "--verified"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                return self._parse_agent_result(result.stdout, default_status="completed")
            else:
                parsed = self._parse_agent_result(result.stdout, default_status="failed")
                if parsed.get("status") != "failed" or parsed.get("error"):
                    return parsed
                return {
                    "status": "failed",
                    "error": result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "failed",
                "error": "Publisher timeout"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def _save_state(self, state: WorkflowState):
        """保存工作流状态"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state_to_dict(state), f, ensure_ascii=False, indent=2)

    def _parse_agent_result(self, stdout: str, default_status: str) -> Dict:
        """Extract the final JSON object from an agent process that also prints logs."""
        text = stdout.strip()
        if not text:
            return {"status": default_status}

        decoder = json.JSONDecoder()
        for index in range(len(text) - 1, -1, -1):
            if text[index] != "{":
                continue
            try:
                parsed, end = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if text[index + end:].strip() == "" and isinstance(parsed, dict):
                return parsed

        return {"status": default_status, "output": stdout}

    def _state_to_dict(self, state: WorkflowState) -> Dict:
        """将状态对象转换为字典"""
        return {
            "workflow_id": state.workflow_id,
            "started_at": state.started_at,
            "current_step": state.current_step,
            "generator_status": state.generator_status,
            "verifier_status": state.verifier_status,
            "publisher_status": state.publisher_status,
            "retry_count": state.retry_count,
            "max_retries": state.max_retries,
            "report_path": state.report_path,
            "verification_report_path": state.verification_report_path,
            "final_status": state.final_status,
            "error_message": state.error_message
        }

    def _finalize(self, state: WorkflowState) -> Dict:
        """最终化工作流"""
        print("\n" + "=" * 60)
        print("📋 工作流执行总结")
        print("=" * 60)

        summary = self._state_to_dict(state)

        print(f"工作流 ID: {summary['workflow_id']}")
        print(f"Generator: {summary['generator_status']}")
        print(f"Verifier: {summary['verifier_status']}")
        print(f"Publisher: {summary['publisher_status']}")
        print(f"重试次数: {summary['retry_count']}/{summary['max_retries']}")
        print(f"最终状态: {summary['final_status']}")

        if summary['error_message']:
            print(f"错误信息: {summary['error_message']}")

        if summary['final_status'] == 'success':
            print("\n🎉 任务完成！报告已发布到 GitHub")
            print(f"📁 报告位置: {summary['report_path']}")
            print(f"🔗 仓库地址: https://github.com/Horacezhang36/Competitive-Analysis")

        # 写入日志
        self._write_log(summary)

        return {
            "status": summary['final_status'],
            "summary": summary
        }

    def _write_log(self, summary: Dict):
        """写入执行日志"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Workflow ID: {summary['workflow_id']}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Status: {summary['final_status']}\n")
            f.write(f"Generator: {summary['generator_status']}\n")
            f.write(f"Verifier: {summary['verifier_status']}\n")
            f.write(f"Publisher: {summary['publisher_status']}\n")
            f.write(f"Retries: {summary['retry_count']}/{summary['max_retries']}\n")
            if summary.get('error_message'):
                f.write(f"Error: {summary['error_message']}\n")
            f.write(f"{'='*60}\n")


def main():
    """主函数"""
    print("🚀 启动竞品分析 Multi-Agent 系统\n")

    agent = OrchestratorAgent()
    result = agent.run()

    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
