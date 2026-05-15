#!/usr/bin/env python3
"""
Agent 1: Generator Agent - 竞品分析报告生成器
负责联网搜索 OpenAI、Claude、Google 的 2026 年新品发布信息
生成带超链接的 HTML 竞品分析报告
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# 尝试加载 Matrix MCP
def _mcp_matrix_search(query, count=10):
    """使用 Matrix MCP 进行网络搜索"""
    import subprocess
    try:
        cmd = [
            "mavis", "mcp", "call", "matrix", "matrix_web_search",
            "--query", query,
            "--count", str(count)
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            # 解析 Matrix 返回的结果
            if isinstance(data, dict) and "result" in data:
                return {"results": data["result"]}
            elif isinstance(data, list):
                return {"results": data}
            return {"results": []}
        else:
            return {"results": [], "error": result.stderr}
    except Exception as e:
        return {"results": [], "error": str(e)}

# 备用搜索：使用 requests 直接调用搜索 API
def _fallback_search(query, count=10):
    """备用搜索方法（当 MCP 不可用时）"""
    import urllib.request
    import urllib.parse
    import ssl
    import re

    # 使用 DuckDuckGo HTML 搜索
    try:
        url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        context = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context, timeout=15) as response:
            html = response.read().decode('utf-8', errors='replace')

        results = []

        # 提取搜索结果
        result_pattern = r'<div class="result results_[^"]*"[^>]*>(.*?)</div>\s*</div>'
        search_results = re.findall(result_pattern, html, re.DOTALL)

        for result_html in search_results[:count]:
            # 提取链接和标题
            link_match = re.search(
                r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
                result_html
            )
            # 提取摘要
            snippet_match = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([^<]+)</a>', result_html)

            if link_match:
                url = link_match.group(1)
                title = link_match.group(2).strip()
                # 清理 HTML 实体
                title = title.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')
                snippet = snippet_match.group(1).strip() if snippet_match else f"关于 {title} 的搜索结果"
                snippet = snippet.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:200] if snippet else f"搜索结果"
                })

        return {"results": results} if results else {"results": [], "error": "No results found"}
    except Exception as e:
        print(f"[Generator] Fallback search error: {e}")
        return {"results": [], "error": str(e)}

class GeneratorAgent:
    """竞品分析报告生成器"""

    def __init__(self):
        self.name = "generator"
        self.status = "pending"
        self.report_path = REPORTS_DIR / "competitive_analysis_report.html"
        self.search_results = {}
        self.max_retries = 3

    def run(self, retry_count=0):
        """执行报告生成任务"""
        self.status = "running"
        print(f"[Generator] Starting report generation (attempt {retry_count + 1})...")

        try:
            # 1. 搜索三家公司的信息
            self._search_competitors()

            # 2. 生成 HTML 报告
            self._generate_html_report()

            # 3. 保存报告
            self._save_report()

            self.status = "completed"
            print(f"[Generator] Report generated successfully: {self.report_path}")
            return {"status": "completed", "report_path": str(self.report_path)}

        except Exception as e:
            print(f"[Generator] Error: {e}")
            if retry_count < self.max_retries - 1:
                print(f"[Generator] Retrying in 5 seconds...")
                import time
                time.sleep(5)
                return self.run(retry_count + 1)
            else:
                self.status = "failed"
                self._log_error(str(e))
                return {"status": "failed", "error": str(e)}

    def _search_competitors(self):
        """搜索三家公司的产品发布信息"""
        print("[Generator] Searching for competitor information...")

        # 定义搜索查询
        searches = {
            "openai": "OpenAI 2026 new products features announcement",
            "claude": "Claude Anthropic 2026 new AI features updates",
            "google": "Google AI Gemini 2026 new features release"
        }

        # 并行搜索
        for company, query in searches.items():
            print(f"[Generator] Searching {company}...")
            try:
                # 先尝试使用 Matrix MCP
                result = _mcp_matrix_search(query, count=10)
                if result.get("results"):
                    self.search_results[company] = result
                else:
                    # 使用备用搜索
                    print(f"[Generator] Matrix MCP not available, using fallback search...")
                    result = _fallback_search(query, count=10)
                    self.search_results[company] = result
            except Exception as e:
                print(f"[Generator] Search error for {company}: {e}")
                self.search_results[company] = {"error": str(e), "results": []}

        print(f"[Generator] Search completed for all competitors")

    def _generate_html_report(self):
        """生成 HTML 报告"""
        print("[Generator] Generating HTML report...")

        html_content = self._create_html_template()

        # 填充搜索结果
        html_content = self._populate_company_section(
            html_content,
            "openai",
            "OpenAI",
            self.search_results.get("openai", {}).get("results", [])
        )
        html_content = self._populate_company_section(
            html_content,
            "claude",
            "Claude (Anthropic)",
            self.search_results.get("claude", {}).get("results", [])
        )
        html_content = self._populate_company_section(
            html_content,
            "google",
            "Google AI",
            self.search_results.get("google", {}).get("results", [])
        )

        self.html_content = html_content
        print("[Generator] HTML report generated")

    def _create_html_template(self):
        """创建 HTML 报告模板"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 竞品分析报告 - 2026年上半年</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            margin-bottom: 30px;
        }}
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .meta {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .meta p {{
            margin: 5px 0;
            color: #666;
        }}
        nav {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        nav ul {{
            list-style: none;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        nav a {{
            color: #667eea;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 20px;
            background: #f0f0ff;
            transition: all 0.3s;
        }}
        nav a:hover {{
            background: #667eea;
            color: white;
        }}
        .company-section {{
            background: white;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .company-header {{
            padding: 20px;
            color: white;
        }}
        .company-header.openai {{ background: linear-gradient(135deg, #412a75 0%, #6b3fa0 100%); }}
        .company-header.claude {{ background: linear-gradient(135deg, #8b4513 0%, #cd853f 100%); }}
        .company-header.google {{ background: linear-gradient(135deg, #4285f4 0%, #34a853 100%); }}
        .company-header h2 {{
            font-size: 1.8em;
            margin-bottom: 5px;
        }}
        .company-header .tagline {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        .company-content {{
            padding: 20px;
        }}
        .product-item {{
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            background: #fafafa;
        }}
        .product-item h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        .product-item p {{
            color: #666;
            margin-bottom: 10px;
        }}
        .product-item .source {{
            font-size: 0.85em;
            color: #999;
        }}
        .product-item .source a {{
            color: #667eea;
            text-decoration: none;
        }}
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .comparison-table th, .comparison-table td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .comparison-table th {{
            background: #667eea;
            color: white;
        }}
        .comparison-table tr:hover {{
            background: #f5f5f5;
        }}
        .summary-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .summary-section h2 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
        }}
        .loading {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .error {{
            background: #ffe6e6;
            color: #c00;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🤖 AI 竞品分析报告</h1>
        <div class="subtitle">OpenAI · Claude (Anthropic) · Google AI</div>
    </header>

    <div class="container">
        <div class="meta">
            <p><strong>📅 报告时间:</strong> 2026年1月 - 5月</p>
            <p><strong>🔄 生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>📊 分析范围:</strong> 三大AI公司新品发布、产品功能、竞争力优势</p>
        </div>

        <nav>
            <ul>
                <li><a href="#openai">OpenAI</a></li>
                <li><a href="#claude">Claude (Anthropic)</a></li>
                <li><a href="#google">Google AI</a></li>
                <li><a href="#comparison">功能对比</a></li>
                <li><a href="#summary">总结</a></li>
            </ul>
        </nav>

        <div class="company-section" id="openai">
            <div class="company-header openai">
                <h2>🔵 OpenAI</h2>
                <div class="tagline">推动 AI 技术的边界</div>
            </div>
            <div class="company-content">
                <div class="loading">正在加载 OpenAI 相关内容...</div>
            </div>
        </div>

        <div class="company-section" id="claude">
            <div class="company-header claude">
                <h2>🟠 Claude (Anthropic)</h2>
                <div class="tagline">构建安全、有益的 AI 系统</div>
            </div>
            <div class="company-content">
                <div class="loading">正在加载 Claude 相关内容...</div>
            </div>
        </div>

        <div class="company-section" id="google">
            <div class="company-header google">
                <h2>🟢 Google AI</h2>
                <div class="tagline">让 AI 惠及每个人</div>
            </div>
            <div class="company-content">
                <div class="loading">正在加载 Google AI 相关内容...</div>
            </div>
        </div>

        <div class="summary-section" id="comparison">
            <h2>📊 产品功能对比</h2>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>功能特性</th>
                        <th>OpenAI</th>
                        <th>Claude</th>
                        <th>Google AI</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>多模态能力</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>长上下文窗口</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>API 可用性</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>定价策略</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>特色功能</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="summary-section" id="summary">
            <h2>📝 竞争力分析总结</h2>
            <div class="loading">正在生成总结...</div>
        </div>

        <footer>
            <p>本报告由 AI Agent 自动生成 · 数据来源：公开网络搜索</p>
            <p>⚠️ 免责声明：报告中包含的信息基于网络搜索结果，可能存在时效性偏差</p>
        </footer>
    </div>
</body>
</html>"""

    def _populate_company_section(self, html, section_id, company_name, results):
        """填充公司内容到 HTML"""
        if not results:
            content_html = f'''
                <div class="error">
                    <p>⚠️ 暂时无法获取 {company_name} 的最新信息。请稍后重试或检查网络连接。</p>
                </div>
            '''
        else:
            content_items = []
            for i, item in enumerate(results[:5]):  # 最多显示5条
                title = item.get("title", "未命名")
                snippet = item.get("snippet", "暂无描述")
                url = item.get("url", "#")

                content_items.append(f'''
                    <div class="product-item">
                        <h3>{title}</h3>
                        <p>{snippet}</p>
                        <div class="source">🔗 来源: <a href="{url}" target="_blank">{url[:60]}...</a></div>
                    </div>
                ''')
            content_html = "\n".join(content_items)

        # 替换占位符
        html = html.replace(
            f'<div class="company-section" id="{section_id}">\n            <div class="company-header {"openai" if section_id == "openai" else "claude" if section_id == "claude" else "google"}">\n                <h2>',
            f'<div class="company-section" id="{section_id}">\n            <div class="company-header {section_id}">\n                <h2>'
        )

        # 找到对应的 company-content 并替换
        start_marker = f'<div class="company-section" id="{section_id}">'
        end_marker = f'<div class="company-section" id="'
        start_idx = html.find(start_marker)
        end_idx = html.find(end_marker, start_idx + 1)

        if start_idx != -1 and end_idx != -1:
            section = html[start_idx:end_idx]
            old_content = f'''
            <div class="company-content">
                <div class="loading">正在加载 {company_name} 相关内容...</div>
            </div>
        '''
            new_content = f'''
            <div class="company-content">
                {content_html}
            </div>
        '''
            html = html.replace(old_content, new_content, 1)

        return html

    def _save_report(self):
        """保存报告"""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(self.html_content)

        print(f"[Generator] Report saved to: {self.report_path}")

    def _log_error(self, error_msg):
        """记录错误日志"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        error_log = LOGS_DIR / "generator_errors.log"

        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] ERROR: {error_msg}\n")


def main():
    """主函数"""
    agent = GeneratorAgent()
    result = agent.run()

    # 输出 JSON 格式结果供 Orchestrator 解析
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())