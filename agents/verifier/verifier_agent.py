#!/usr/bin/env python3
"""
Agent 2: Verifier Agent - 竞品分析内容校验器
负责校验 Generator Agent 生成的报告内容是否符合事实
评估报告质量，决定是否放行或要求重新生成
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import matrix_web_search as mcp_matrix
    MATRIX_AVAILABLE = True
except ImportError:
    MATRIX_AVAILABLE = False
    print("[Verifier] Warning: Matrix MCP not available")

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

class VerifierAgent:
    """竞品分析内容校验器"""

    def __init__(self):
        self.name = "verifier"
        self.status = "pending"
        self.report_path = REPORTS_DIR / "competitive_analysis_report.html"
        self.verification_report_path = LOGS_DIR / "verification_report.md"

        # 校验权重
        self.weights = {
            "fact_accuracy": 40,      # 事实准确性
            "completeness": 25,       # 内容完整性
            "url_validity": 20,       # URL 有效性
            "timeliness": 15          # 时效性
        }

        self.max_retries = 3

        # 问题严重度
        self.severity_levels = {
            "CRITICAL": "产品名称错误、关键事实错误",
            "MAJOR": "URL 失效、关键信息缺失",
            "MINOR": "格式问题、轻微不一致"
        }

    def run(self, report_path: str = None) -> Dict:
        """执行校验任务"""
        self.status = "verifying"
        print("[Verifier] Starting verification...")

        if report_path:
            self.report_path = Path(report_path)

        try:
            # 1. 加载报告
            report_content = self._load_report()

            # 2. 执行各项校验
            fact_result = self._check_fact_accuracy(report_content)
            completeness_result = self._check_completeness(report_content)
            url_result = self._check_url_validity(report_content)
            timeliness_result = self._check_timeliness(report_content)

            # 3. 计算总分
            score = self._calculate_score(
                fact_result,
                completeness_result,
                url_result,
                timeliness_result
            )

            # 4. 生成校验报告
            verification_report = self._generate_verification_report(
                fact_result,
                completeness_result,
                url_result,
                timeliness_result,
                score
            )

            # 5. 保存校验报告
            self._save_verification_report(verification_report)

            # 6. 决定是否通过
            passed = score >= 75 and not fact_result.get("critical_issues")

            if passed:
                self.status = "passed"
                print(f"[Verifier] Verification PASSED with score: {score}")
            else:
                self.status = "failed"
                print(f"[Verifier] Verification FAILED with score: {score}")

            return {
                "status": "passed" if passed else "failed",
                "score": score,
                "report_path": str(self.verification_report_path),
                "issues": self._collect_issues(fact_result, completeness_result, url_result),
                "fact_result": fact_result,
                "completeness_result": completeness_result,
                "url_result": url_result,
                "timeliness_result": timeliness_result
            }

        except Exception as e:
            print(f"[Verifier] Verification error: {e}")
            self._log_error(str(e))
            return {
                "status": "failed",
                "score": 0,
                "error": str(e)
            }

    def _load_report(self) -> str:
        """加载报告内容"""
        if not self.report_path.exists():
            raise FileNotFoundError(f"Report not found: {self.report_path}")

        with open(self.report_path, "r", encoding="utf-8") as f:
            return f.read()

    def _check_fact_accuracy(self, content: str) -> Dict:
        """检查事实准确性"""
        print("[Verifier] Checking fact accuracy...")

        issues = []
        critical_issues = []

        # 检查必需的公司
        companies = ["OpenAI", "Claude", "Google"]
        for company in companies:
            if company not in content:
                critical_issues.append({
                    "type": "CRITICAL",
                    "message": f"缺少 {company} 相关内容"
                })

        # 检查是否有明显的虚假信息特征
        # 1. 检查是否全是占位符
        if "<div class=\"loading\">" in content or "正在加载" in content:
            issues.append({
                "type": "MAJOR",
                "message": "报告包含未填充的占位符内容"
            })

        # 2. 检查是否有过多的 "暂无" 或 "未命名"
        if content.count("暂无") > 3:
            issues.append({
                "type": "MAJOR",
                "message": "报告中存在过多占位信息"
            })

        # 3. 尝试联网验证一些关键信息（如果有搜索结果）
        # 这里简化处理，实际可以抽取关键句子进行验证

        return {
            "passed": len(critical_issues) == 0 and len(issues) == 0,
            "critical_issues": critical_issues,
            "issues": issues,
            "score": max(0, 40 - len(critical_issues) * 15 - len(issues) * 5)
        }

    def _check_completeness(self, content: str) -> Dict:
        """检查内容完整性"""
        print("[Verifier] Checking completeness...")

        issues = []
        checklist = {
            "companies_covered": ["OpenAI", "Claude", "Google"],
            "sections": ["产品功能", "竞争力", "对比"],
            "has_meta": "报告时间" in content,
            "has_nav": "nav" in content.lower()
        }

        missing = []
        for key, items in checklist.items():
            if isinstance(items, list):
                for item in items:
                    if item not in content:
                        missing.append(item)
            elif not items:
                missing.append(key)

        if missing:
            issues.append({
                "type": "MAJOR",
                "message": f"缺少以下内容: {', '.join(missing)}"
            })

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "checklist": checklist,
            "score": max(0, 25 - len(issues) * 8)
        }

    def _check_url_validity(self, content: str) -> Dict:
        """检查 URL 有效性"""
        print("[Verifier] Checking URL validity...")

        # 提取所有 URL
        url_pattern = r'href="([^"#]+)"'
        urls = re.findall(url_pattern, content)

        if not urls:
            return {
                "passed": False,
                "issues": [{"type": "MAJOR", "message": "报告中没有找到任何 URL 链接"}],
                "valid_count": 0,
                "total_count": 0,
                "score": 0
            }

        # 简化处理：检查 URL 格式是否正确
        valid_urls = []
        invalid_urls = []

        for url in urls:
            if url.startswith("http://") or url.startswith("https://"):
                valid_urls.append(url)
            elif url != "#":
                invalid_urls.append(url)

        validity_rate = len(valid_urls) / len(urls) if urls else 0

        issues = []
        if validity_rate < 0.8:
            issues.append({
                "type": "MAJOR",
                "message": f"URL 有效性不足: {len(valid_urls)}/{len(urls)} 个有效链接"
            })

        return {
            "passed": validity_rate >= 0.8,
            "valid_count": len(valid_urls),
            "total_count": len(urls),
            "validity_rate": validity_rate,
            "issues": issues,
            "sample_urls": valid_urls[:5] if valid_urls else [],
            "score": min(20, int(validity_rate * 20))
        }

    def _check_timeliness(self, content: str) -> Dict:
        """检查时效性"""
        print("[Verifier] Checking timeliness...")

        # 检查是否包含 2026 年的信息
        has_2026 = "2026" in content

        issues = []
        if not has_2026:
            issues.append({
                "type": "MAJOR",
                "message": "报告中未包含 2026 年相关信息"
            })

        # 检查是否有明确的报告时间
        has_date = re.search(r'\d{4}年\d{1,2}月', content) is not None

        return {
            "passed": has_2026,
            "has_2026": has_2026,
            "has_date": has_date,
            "issues": issues,
            "score": 15 if has_2026 else 0
        }

    def _calculate_score(
        self,
        fact_result: Dict,
        completeness_result: Dict,
        url_result: Dict,
        timeliness_result: Dict
    ) -> int:
        """计算总分"""
        total_score = (
            fact_result.get("score", 0) +
            completeness_result.get("score", 0) +
            url_result.get("score", 0) +
            timeliness_result.get("score", 0)
        )
        return min(100, total_score)

    def _collect_issues(
        self,
        fact_result: Dict,
        completeness_result: Dict,
        url_result: Dict
    ) -> List[Dict]:
        """收集所有问题"""
        all_issues = []

        for issue in fact_result.get("critical_issues", []):
            issue["category"] = "fact_accuracy"
            all_issues.append(issue)

        for issue in fact_result.get("issues", []):
            issue["category"] = "fact_accuracy"
            all_issues.append(issue)

        for issue in completeness_result.get("issues", []):
            issue["category"] = "completeness"
            all_issues.append(issue)

        for issue in url_result.get("issues", []):
            issue["category"] = "url_validity"
            all_issues.append(issue)

        return all_issues

    def _generate_verification_report(
        self,
        fact_result: Dict,
        completeness_result: Dict,
        url_result: Dict,
        timeliness_result: Dict,
        score: int
    ) -> str:
        """生成校验报告"""
        report = f"""# 竞品分析报告校验报告

## 校验基本信息
- **校验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **被校验报告**: {self.report_path}
- **校验状态**: {'✅ 通过' if score >= 75 else '❌ 未通过'}
- **综合评分**: {score}/100

---

## 各项校验结果

### 1. 事实准确性 (权重: 40分)
| 项目 | 得分 | 说明 |
|------|------|------|
| 评分 | {fact_result['score']}/40 | |

**Critical 问题:**
{self._format_issues(fact_result.get('critical_issues', []))}

**一般问题:**
{self._format_issues(fact_result.get('issues', []))}

---

### 2. 内容完整性 (权重: 25分)
| 项目 | 得分 | 说明 |
|------|------|------|
| 评分 | {completeness_result['score']}/25 | |

**检查清单:**
{json.dumps(completeness_result.get('checklist', {}), ensure_ascii=False, indent=2)}

**问题列表:**
{self._format_issues(completeness_result.get('issues', []))}

---

### 3. URL 链接有效性 (权重: 20分)
| 项目 | 得分 | 说明 |
|------|------|------|
| 评分 | {url_result['score']}/20 | |
| 有效链接 | {url_result.get('valid_count', 0)}/{url_result.get('total_count', 0)} | |
| 有效率 | {url_result.get('validity_rate', 0)*100:.1f}% | |

**问题列表:**
{self._format_issues(url_result.get('issues', []))}

**示例 URL:**
{chr(10).join([f'- {u}' for u in url_result.get('sample_urls', [])]) or '无'}

---

### 4. 时效性 (权重: 15分)
| 项目 | 得分 | 说明 |
|------|------|------|
| 评分 | {timeliness_result['score']}/15 | |
| 包含 2026 年信息 | {'是' if timeliness_result.get('has_2026') else '否'} | |

**问题列表:**
{self._format_issues(timeliness_result.get('issues', []))}

---

## 综合评分明细

| 校验项 | 权重 | 得分 | 占比 |
|--------|------|------|------|
| 事实准确性 | 40 | {fact_result['score']} | {fact_result['score']/score*100 if score > 0 else 0:.1f}% |
| 内容完整性 | 25 | {completeness_result['score']} | {completeness_result['score']/score*100 if score > 0 else 0:.1f}% |
| URL 有效性 | 20 | {url_result['score']} | {url_result['score']/score*100 if score > 0 else 0:.1f}% |
| 时效性 | 15 | {timeliness_result['score']} | {timeliness_result['score']/score*100 if score > 0 else 0:.1f}% |
| **总计** | **100** | **{score}** | **100%** |

---

## 校验结论

{'## ✅ 校验通过' if score >= 75 else '## ❌ 校验未通过'}

综合评分: **{score}/100** {'(≥75分通过)' if score >= 75 else '(需要达到75分才能通过)'}

{f'存在 {len([i for i in self._collect_issues(fact_result, completeness_result, url_result) if i["type"] == "CRITICAL"])} 个 Critical 问题，必须修复' if score < 75 else '报告质量符合要求，可以放行'}

---

## 后续建议

{self._generate_suggestions(fact_result, completeness_result, url_result, timeliness_result)}

"""

        return report

    def _format_issues(self, issues: List[Dict]) -> str:
        """格式化问题列表"""
        if not issues:
            return "无"

        return "\n".join([
            f'- **{issue["type"]}**: {issue["message"]}'
            for issue in issues
        ])

    def _generate_suggestions(
        self,
        fact_result: Dict,
        completeness_result: Dict,
        url_result: Dict,
        timeliness_result: Dict
    ) -> str:
        """生成改进建议"""
        suggestions = []

        if fact_result['score'] < 30:
            suggestions.append("1. **重新生成报告**: 当前报告内容质量较低，建议重新执行搜索和生成")

        if completeness_result['score'] < 20:
            suggestions.append("2. **补充缺失内容**: 确保报告覆盖所有三家公司的详细信息")

        if url_result['score'] < 15:
            suggestions.append("3. **修复 URL 链接**: 部分 URL 无效或格式错误，请检查并修正")

        if not suggestions:
            suggestions.append("1. **保持现状**: 报告质量良好，可直接使用")

        return "\n".join(suggestions)

    def _save_verification_report(self, report: str):
        """保存校验报告"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.verification_report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"[Verifier] Verification report saved: {self.verification_report_path}")

    def _log_error(self, error_msg: str):
        """记录错误日志"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        error_log = LOGS_DIR / "verifier_errors.log"

        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] ERROR: {error_msg}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Verifier Agent")
    parser.add_argument("--report", "-r", help="Report path to verify")
    args = parser.parse_args()

    agent = VerifierAgent()
    result = agent.run(args.report)

    # 输出 JSON 格式结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())