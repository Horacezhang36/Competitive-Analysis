#!/usr/bin/env python3
"""
Agent 5: Scheduler Agent - 定时任务调度器 + 新品检测器
每天扫描 OpenAI/Google/Claude 官方渠道，检测新品发布并触发工作流
"""

import json
import os
import sys
import ssl
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LAST_SCAN_FILE = LOGS_DIR / "last_scan.json"
DETECTION_LOG = LOGS_DIR / "latest_detection.md"


class SchedulerAgent:
    """定时任务调度器 + 新品检测器"""

    def __init__(self):
        self.name = "scheduler"
        self.status = "idle"
        self.max_retries = 3

        # 官方数据源
        self.sources = {
            "openai": {
                "name": "OpenAI",
                "urls": [
                    "https://openai.com/blog",
                    "https://openai.com/news/",
                ],
                "keywords": ["new", "release", "announce", "launch", "introducing", "gpt", "sora", "operator", "o3", "gpt-5"]
            },
            "google": {
                "name": "Google AI",
                "urls": [
                    "https://blog.google/technology/ai/",
                    "https://deepmind.google",
                ],
                "keywords": ["new", "launch", "gemini", "veo", "imagen", "alpha", "project", "2026", "announce"]
            },
            "claude": {
                "name": "Claude (Anthropic)",
                "urls": [
                    "https://www.anthropic.com/news",
                    "https://docs.anthropic.com",
                ],
                "keywords": ["new", "claude", "release", "update", "version", "2026", "announce", "code", "haiku", "sonnet", "opus"]
            }
        }

    def run(self) -> Dict:
        """执行扫描任务"""
        self.status = "scanning"
        print("=" * 60)
        print("⏰ Scheduler Agent - 定时扫描启动")
        print("=" * 60)
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # 1. 获取上次扫描记录
            last_scan = self._load_last_scan()

            # 2. 扫描所有渠道
            scan_results = self._scan_all_sources()

            # 3. 检测新品
            new_products = self._detect_new_products(scan_results, last_scan)

            # 4. 保存扫描记录
            self._save_scan_record(scan_results)

            # 5. 生成检测报告
            detection_report = self._generate_detection_report(scan_results, new_products)

            # 6. 决策
            if new_products:
                print(f"\n🎉 检测到 {len(new_products)} 个新品/更新！")
                self.status = "triggering"

                # 触发工作流
                trigger_result = self._trigger_workflow(new_products)

                return {
                    "status": "triggered",
                    "new_products_count": len(new_products),
                    "new_products": new_products,
                    "trigger_result": trigger_result
                }
            else:
                print("\n😴 未检测到新品，静默退出")
                self.status = "completed"

                return {
                    "status": "completed",
                    "new_products_count": 0,
                    "message": "No new products detected"
                }

        except Exception as e:
            print(f"[Scheduler] Error: {e}")
            self.status = "failed"
            return {"status": "failed", "error": str(e)}

    def _scan_all_sources(self) -> Dict:
        """扫描所有数据源"""
        results = {}

        for company, config in self.sources.items():
            print(f"\n🔍 扫描 {config['name']}...")
            company_results = []

            for url in config["urls"]:
                content = self._fetch_page(url)
                if content:
                    # 提取新闻条目
                    items = self._extract_news_items(content, url)
                    company_results.extend(items)

            # 去重
            seen = set()
            unique = []
            for item in company_results:
                key = item.get("title", "") + item.get("url", "")
                if key not in seen:
                    seen.add(key)
                    unique.append(item)

            results[company] = {
                "name": config["name"],
                "items": unique,
                "count": len(unique)
            }
            print(f"   找到 {len(unique)} 条新闻")

        return results

    def _fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        import urllib.request

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            context = ssl.create_default_context()
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=context, timeout=15) as response:
                return response.read().decode('utf-8', errors='replace')
        except Exception as e:
            print(f"   获取失败 {url}: {e}")
            return None

    def _extract_news_items(self, content: str, base_url: str) -> List[Dict]:
        """从页面提取新闻条目"""
        items = []

        # 简单模式匹配 - 提取标题和链接
        # 实际生产中应该使用更智能的解析
        patterns = [
            r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*post[^"]*"[^>]*>([^<]+)</a>',
            r'<h[23][^>]*>([^<]+)</h[23]>',
            r'<article[^>]*>(.*?)</article>',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    url = match[0]
                    title = match[1].strip()
                    if url and title and len(title) > 5:
                        items.append({
                            "title": re.sub(r'<[^>]+>', '', title),
                            "url": url if url.startswith('http') else base_url,
                            "date": datetime.now().strftime('%Y-%m-%d')
                        })

        return items[:20]  # 限制数量

    def _detect_new_products(self, scan_results: Dict, last_scan: Optional[Dict]) -> List[Dict]:
        """检测新品"""
        new_products = []

        for company, data in scan_results.items():
            last_items = last_scan.get(company, {}).get("items", []) if last_scan else []
            last_titles = set(item.get("title", "") for item in last_items)

            for item in data.get("items", []):
                title = item.get("title", "")
                if title not in last_titles:
                    # 检查关键词
                    keywords = self.sources[company]["keywords"]
                    if any(kw.lower() in title.lower() for kw in keywords):
                        new_products.append({
                            **item,
                            "company": company,
                            "company_name": data["name"]
                        })

        return new_products

    def _load_last_scan(self) -> Optional[Dict]:
        """加载上次扫描记录"""
        if LAST_SCAN_FILE.exists():
            try:
                with open(LAST_SCAN_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None

    def _save_scan_record(self, scan_results: Dict):
        """保存扫描记录"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": datetime.now().isoformat(),
            "companies": scan_results
        }

        with open(LAST_SCAN_FILE, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    def _generate_detection_report(self, scan_results: Dict, new_products: List[Dict]) -> str:
        """生成检测报告"""
        report = f"""# AI 产品检测报告

## 扫描信息
- **扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **状态**: {"检测到新品" if new_products else "无新品"}

---

## 扫描结果

| 公司 | 新闻数量 |
|------|---------|
| OpenAI | {scan_results.get('openai', {}).get('count', 0)} |
| Google AI | {scan_results.get('google', {}).get('count', 0)} |
| Claude | {scan_results.get('claude', {}).get('count', 0)} |

---

## 新品列表

{"## 检测到以下新品/更新" if new_products else "## 未检测到新品"}\n
"""

        if new_products:
            for i, product in enumerate(new_products, 1):
                report += f"""
### {i}. {product.get('title', 'Unknown')}

- **公司**: {product.get('company_name', product.get('company', 'Unknown'))}
- **链接**: {product.get('url', 'N/A')}
- **发现时间**: {product.get('date', datetime.now().strftime('%Y-%m-%d'))}
"""
        else:
            report += "\n本次扫描未发现新的产品发布或重大更新。"

        with open(DETECTION_LOG, "w", encoding="utf-8") as f:
            f.write(report)

        return report

    def _trigger_workflow(self, new_products: List[Dict]) -> Dict:
        """触发工作流"""
        print("\n🚀 触发 Multi-Agent 工作流...")

        # 导入并运行 Orchestrator
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "agents" / "orchestrator"))
            from orchestrator_agent import OrchestratorAgent

            orchestrator = OrchestratorAgent()
            result = orchestrator.run()

            return result

        except Exception as e:
            print(f"[Scheduler] Workflow trigger error: {e}")
            return {"status": "error", "error": str(e)}


def main():
    agent = SchedulerAgent()
    result = agent.run()
    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in ["completed", "triggered"] else 1


if __name__ == "__main__":
    sys.exit(main())