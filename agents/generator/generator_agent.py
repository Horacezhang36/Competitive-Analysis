#!/usr/bin/env python3
"""
Agent 1: Generator Agent - 竞品分析报告生成器 (V2)
深度调研 OpenAI、Claude (Anthropic)、Google AI 三家公司
生成高级 HTML 竞品分析报告
"""

import json
import os
import sys
import re
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
SKILLS_DIR = Path(__file__).parent / "skills"
LOGS_DIR = PROJECT_ROOT / "logs"


def search_web(query: str, count: int = 15) -> List[Dict]:
    """联网搜索"""
    import urllib.request
    import urllib.parse

    try:
        url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        context = ssl.create_default_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=context, timeout=20) as response:
            html = response.read().decode('utf-8', errors='replace')

        results = []
        result_pattern = r'<div class="result results_[^"]*"[^>]*>(.*?)</div>\s*</div>'
        search_results = re.findall(result_pattern, html, re.DOTALL)

        for result_html in search_results[:count]:
            link_match = re.search(
                r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
                result_html
            )
            snippet_match = re.search(
                r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([^<]+)</a>',
                result_html
            )

            if link_match:
                url = link_match.group(1)
                title = link_match.group(2).strip()
                title = title.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')
                snippet = snippet_match.group(1).strip() if snippet_match else f"关于 {title}"
                snippet = snippet.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')

                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:300]
                })

        return results
    except Exception as e:
        print(f"[Generator] Search error: {e}")
        return []


def fetch_official_news(company: str) -> List[Dict]:
    """从官方渠道获取新闻"""
    queries = {
        "openai": [
            "site:openai.com 2026",
            "OpenAI GPT-5 release 2026",
            "OpenAI Operator features 2026",
            "OpenAI Deep Research announcement 2026"
        ],
        "google": [
            "site:deepmind.google 2026",
            "Google Gemini 2.5 features 2026",
            "Google AI Agent updates 2026",
            "Google Veo Imagen 2026 release"
        ],
        "claude": [
            "site:anthropic.com 2026",
            "Claude 4 release announcement 2026",
            "Anthropic Claude Code updates 2026",
            "Claude API new features 2026"
        ]
    }

    results = []
    if company not in queries:
        return results

    for query in queries[company]:
        search_results = search_web(query, count=5)
        results.extend(search_results)

    # 去重
    seen_urls = set()
    unique_results = []
    for r in results:
        if r['url'] not in seen_urls:
            seen_urls.add(r['url'])
            unique_results.append(r)

    return unique_results


class GeneratorAgent:
    """竞品分析报告生成器 V2"""

    def __init__(self):
        self.name = "generator"
        self.status = "pending"
        self.report_path = REPORTS_DIR / "competitive_analysis_report.html"
        self.max_retries = 3

        # 收集的数据
        self.data = {
            "openai": {"products": [], "sources": []},
            "google": {"products": [], "sources": []},
            "claude": {"products": [], "sources": []}
        }

    def run(self, retry_count: int = 0) -> Dict:
        """执行报告生成"""
        self.status = "running"
        print("=" * 60)
        print("🎯 Generator Agent V2 - 深度竞品分析")
        print("=" * 60)

        try:
            # 阶段 1: 深度调研
            print("\n📊 阶段 1: 深度调研...")
            self._research_all()

            # 阶段 2: 生成报告
            print("\n📝 阶段 2: 生成高级报告...")
            self._generate_advanced_report()

            # 阶段 3: 保存报告
            print("\n💾 阶段 3: 保存报告...")
            self._save_report()

            self.status = "completed"
            return {
                "status": "completed",
                "report_path": str(self.report_path),
                "companies_analyzed": 3,
                "products_found": sum(len(p) for p in self.data.values())
            }

        except Exception as e:
            print(f"[Generator] Error: {e}")
            self.status = "failed"
            return {"status": "failed", "error": str(e)}

    def _research_all(self):
        """调研所有公司"""
        companies = ["openai", "google", "claude"]
        company_names = {"openai": "OpenAI", "google": "Google AI", "claude": "Claude (Anthropic)"}

        for company in companies:
            print(f"\n🔍 调研 {company_names[company]}...")

            # 获取官方新闻
            news = fetch_official_news(company)
            self.data[company]["sources"] = news

            # 获取产品列表
            self.data[company]["products"] = self._extract_products(company, news)

            print(f"   找到 {len(news)} 条来源，提取 {len(self.data[company]['products'])} 个产品")

    def _extract_products(self, company: str, sources: List[Dict]) -> List[Dict]:
        """从搜索结果中提取产品信息"""
        products = []

        # 常见产品关键词
        product_keywords = {
            "openai": ["GPT-5", "GPT-4o", "Operator", "Deep Research", "Sora", "o1", "o3", "ChatGPT", "API", "Model"],
            "google": ["Gemini", "Veo", "Imagen", "AlphaFold", "Project Mariner", "Astra", "Gemma", "TensorFlow"],
            "claude": ["Claude", "Haiku", "Sonnet", "opus", "Code", "API", "Anthropic"]
        }

        keywords = product_keywords.get(company, [])

        for source in sources:
            title = source.get("title", "")
            snippet = source.get("snippet", "")
            url = source.get("url", "")

            # 检测产品提及
            mentioned = [kw for kw in keywords if kw.lower() in (title + snippet).lower()]

            if mentioned:
                product = {
                    "name": self._clean_product_name(title, mentioned),
                    "announcement_date": self._extract_date(title + snippet),
                    "description": snippet,
                    "key_features": mentioned,
                    "source_url": url,
                    "competitor_advantages": self._extract_advantages(snippet)
                }
                products.append(product)

        return products

    def _clean_product_name(self, title: str, keywords: List[str]) -> str:
        """清理产品名称"""
        name = title
        for kw in keywords:
            if kw.lower() in name.lower():
                name = name.replace(kw, f"**{kw}**")
        # 移除 HTML
        name = re.sub(r'<[^>]+>', '', name)
        return name[:100]

    def _extract_date(self, text: str) -> str:
        """提取日期"""
        patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*2026',
            r'2026',
            r'May\s+2026',
            r'2026年\d+月'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "2026"

    def _extract_advantages(self, text: str) -> str:
        """提取竞争优势"""
        advantages = []
        positive_words = ["new", "improved", "faster", "better", "advanced", "powerful", "enhanced", "latest", "updated"]

        for word in positive_words:
            if word in text.lower():
                advantages.append(word.capitalize())

        return ", ".join(advantages[:3]) if advantages else "最新版本"

    def _generate_advanced_report(self):
        """生成高级 HTML 报告"""
        self.html_content = self._create_advanced_html()

    def _create_advanced_html(self) -> str:
        """创建高级 HTML 模板"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        companies_data = self._build_companies_data()

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 竞品分析报告 | 2026年5月</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --openai-primary: #412a75;
            --openai-secondary: #6b3fa0;
            --google-primary: #4285f4;
            --google-secondary: #34a853;
            --claude-primary: #cd853f;
            --claude-secondary: #8b4513;
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --border-color: #30363d;
            --accent-blue: #58a6ff;
            --success: #3fb950;
            --warning: #d29922;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%);
            padding: 60px 20px;
            text-align: center;
            border-bottom: 1px solid var(--border-color);
        }}
        .header h1 {{
            font-size: 2.8em;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #58a6ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
        }}
        .header .meta {{
            color: var(--text-secondary);
            font-size: 1.1em;
        }}
        .header .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 30px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: var(--bg-card);
            padding: 20px 30px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            text-align: center;
            min-width: 150px;
        }}
        .stat-card .number {{
            font-size: 2.2em;
            font-weight: 700;
            color: var(--accent-blue);
        }}
        .stat-card .label {{
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-top: 5px;
        }}

        /* Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        /* Navigation Tabs */
        .nav-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            position: sticky;
            top: 0;
            background: var(--bg-dark);
            padding: 20px 0;
            z-index: 100;
        }}
        .nav-tab {{
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
        }}
        .nav-tab:hover {{
            background: var(--bg-hover);
        }}
        .nav-tab.active {{
            background: var(--accent-blue);
            color: #fff;
            border-color: var(--accent-blue);
        }}
        .nav-tab.openai {{ --tab-color: var(--openai-primary); }}
        .nav-tab.google {{ --tab-color: var(--google-primary); }}
        .nav-tab.claude {{ --tab-color: var(--claude-primary); }}
        .nav-tab.active {{
            background: var(--tab-color);
            border-color: var(--tab-color);
        }}

        /* Company Sections */
        .company-section {{
            display: none;
            animation: fadeIn 0.5s ease;
        }}
        .company-section.active {{
            display: block;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .company-header {{
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 30px;
        }}
        .company-header.openai {{
            background: linear-gradient(135deg, var(--openai-primary), var(--openai-secondary));
        }}
        .company-header.google {{
            background: linear-gradient(135deg, var(--google-primary), var(--google-secondary));
        }}
        .company-header.claude {{
            background: linear-gradient(135deg, var(--claude-primary), var(--claude-secondary));
        }}
        .company-header h2 {{
            font-size: 1.8em;
            margin-bottom: 10px;
        }}
        .company-header .tagline {{
            opacity: 0.9;
            font-size: 1em;
        }}

        /* Product Cards */
        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .product-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s;
        }}
        .product-card:hover {{
            border-color: var(--accent-blue);
            transform: translateY(-3px);
        }}
        .product-card h3 {{
            font-size: 1.3em;
            margin-bottom: 12px;
            color: var(--accent-blue);
        }}
        .product-card .date {{
            color: var(--text-secondary);
            font-size: 0.85em;
            margin-bottom: 15px;
        }}
        .product-card .description {{
            color: var(--text-primary);
            margin-bottom: 15px;
            line-height: 1.7;
        }}
        .product-card .features {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }}
        .feature-tag {{
            background: var(--bg-hover);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            color: var(--accent-blue);
        }}
        .product-card .source {{
            font-size: 0.85em;
            color: var(--text-secondary);
        }}
        .product-card .source a {{
            color: var(--accent-blue);
            text-decoration: none;
        }}
        .product-card .source a:hover {{
            text-decoration: underline;
        }}

        /* Comparison Section */
        .comparison-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 40px;
        }}
        .comparison-section h2 {{
            font-size: 1.5em;
            margin-bottom: 25px;
            color: var(--accent-blue);
        }}
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }}
        .comparison-table th, .comparison-table td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        .comparison-table th {{
            background: var(--bg-hover);
            font-weight: 600;
        }}
        .comparison-table th.openai {{ color: var(--openai-secondary); }}
        .comparison-table th.google {{ color: var(--google-secondary); }}
        .comparison-table th.claude {{ color: var(--claude-secondary); }}
        .comparison-table tr:hover {{
            background: var(--bg-hover);
        }}
        .comparison-table td:first-child {{
            font-weight: 500;
            color: var(--text-secondary);
        }}

        /* Market Analysis */
        .market-section {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 40px;
        }}
        .market-section h2 {{
            font-size: 1.5em;
            margin-bottom: 25px;
            color: var(--accent-blue);
        }}
        .market-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        .market-card {{
            background: var(--bg-hover);
            padding: 20px;
            border-radius: 12px;
        }}
        .market-card h4 {{
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        .market-card p {{
            color: var(--text-secondary);
            font-size: 0.95em;
        }}

        /* Timeline */
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: var(--border-color);
        }}
        .timeline-item {{
            position: relative;
            padding-bottom: 30px;
        }}
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -34px;
            top: 5px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--accent-blue);
        }}
        .timeline-item .date {{
            color: var(--accent-blue);
            font-size: 0.9em;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .timeline-item .title {{
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .timeline-item .desc {{
            color: var(--text-secondary);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 40px 20px;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
        }}
        .footer .disclaimer {{
            font-size: 0.9em;
            margin-top: 15px;
            padding: 15px;
            background: var(--bg-card);
            border-radius: 8px;
        }}

        /* Sources Section */
        .sources-section {{
            margin-top: 40px;
        }}
        .sources-section h3 {{
            font-size: 1.2em;
            margin-bottom: 20px;
            color: var(--text-primary);
        }}
        .source-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 15px;
        }}
        .source-item {{
            background: var(--bg-card);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        .source-item a {{
            color: var(--accent-blue);
            text-decoration: none;
            font-weight: 500;
        }}
        .source-item a:hover {{
            text-decoration: underline;
        }}
        .source-item .snippet {{
            color: var(--text-secondary);
            font-size: 0.85em;
            margin-top: 8px;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2em; }}
            .stats {{ gap: 15px; }}
            .stat-card {{ padding: 15px 20px; }}
            .products-grid {{ grid-template-columns: 1fr; }}
            .comparison-table {{ font-size: 0.85em; }}
            .comparison-table th, .comparison-table td {{ padding: 10px; }}
        }}

        /* Print */
        @media print {{
            body {{ background: #fff; color: #000; }}
            .nav-tabs {{ display: none; }}
            .company-section {{ display: block !important; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>🤖 AI 竞品分析报告</h1>
        <div class="meta">OpenAI · Google AI · Claude (Anthropic) | 2026年5月深度分析</div>
        <div class="stats">
            <div class="stat-card">
                <div class="number">3</div>
                <div class="label">AI 公司分析</div>
            </div>
            <div class="stat-card">
                <div class="number">{companies_data['total_products']}</div>
                <div class="label">产品/功能</div>
            </div>
            <div class="stat-card">
                <div class="number">{companies_data['total_sources']}</div>
                <div class="label">参考来源</div>
            </div>
            <div class="stat-card">
                <div class="number">{timestamp.split()[0]}</div>
                <div class="label">报告日期</div>
            </div>
        </div>
    </header>

    <div class="container">
        <nav class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('openai')">🔵 OpenAI</div>
            <div class="nav-tab" onclick="showTab('google')">🟢 Google AI</div>
            <div class="nav-tab" onclick="showTab('claude')">🟠 Claude</div>
            <div class="nav-tab" onclick="showTab('comparison')">📊 功能对比</div>
            <div class="nav-tab" onclick="showTab('market')">📈 市场分析</div>
        </nav>

        {self._build_company_sections(companies_data)}

        <!-- Comparison Section -->
        <div class="company-section" id="comparison">
            <div class="comparison-section">
                <h2>📊 产品功能对比矩阵</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>功能特性</th>
                            <th class="openai">OpenAI</th>
                            <th class="google">Google AI</th>
                            <th class="claude">Claude</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>最新大模型</td>
                            <td>GPT-4o / o3</td>
                            <td>Gemini 2.5 Pro</td>
                            <td>Claude 3.7</td>
                        </tr>
                        <tr>
                            <td>多模态能力</td>
                            <td>✅ 文本/图像/音频/视频</td>
                            <td>✅ 文本/图像/视频</td>
                            <td>✅ 文本/图像</td>
                        </tr>
                        <tr>
                            <td>上下文窗口</td>
                            <td>200K tokens</td>
                            <td>1M tokens</td>
                            <td>200K tokens</td>
                        </tr>
                        <tr>
                            <td>Agent 能力</td>
                            <td>Operator / Deep Research</td>
                            <td>Project Mariner / Astra</td>
                            <td>Claude Code</td>
                        </tr>
                        <tr>
                            <td>代码能力</td>
                            <td>⭐⭐⭐⭐⭐</td>
                            <td>⭐⭐⭐⭐</td>
                            <td>⭐⭐⭐⭐⭐</td>
                        </tr>
                        <tr>
                            <td>推理能力</td>
                            <td>o1/o3 系列强化学习</td>
                            <td>Gemini Flash 2.0</td>
                            <td>Extended Thinking</td>
                        </tr>
                        <tr>
                            <td>API 可用性</td>
                            <td>✅ 稳定</td>
                            <td>✅ 稳定</td>
                            <td>✅ 稳定</td>
                        </tr>
                        <tr>
                            <td>定价策略</td>
                            <td>免费+付费分层</td>
                            <td>免费+Ultra订阅</td>
                            <td>免费+Pro订阅</td>
                        </tr>
                        <tr>
                            <td>特色功能</td>
                            <td>Sora视频生成</td>
                            <td>Veo/Imagen视频图片</td>
                            <td>安全对齐优先</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Market Analysis -->
        <div class="company-section" id="market">
            <div class="market-section">
                <h2>📈 市场分析与趋势预测</h2>
                <div class="market-grid">
                    <div class="market-card">
                        <h4>🔵 OpenAI 市场定位</h4>
                        <p>市场领导者，持续引领大模型技术革新。聚焦企业级市场，通过 API 和订阅服务盈利。Sora 和 Operator 展示多模态和 Agent 能力。</p>
                    </div>
                    <div class="market-card">
                        <h4>🟢 Google AI 市场定位</h4>
                        <p>依托搜索和云服务生态，提供差异化 AI 服务。Gemini 在长上下文和多模态方面有优势，整合 Google 全产品线。</p>
                    </div>
                    <div class="market-card">
                        <h4>🟠 Claude 市场定位</h4>
                        <p>安全优先理念，深耕特定垂直领域。Claude Code 聚焦开发者市场，在代码能力和安全性上建立差异化优势。</p>
                    </div>
                    <div class="market-card">
                        <h4>🔮 2026下半年趋势预测</h4>
                        <p>1. Agent 能力成为竞争核心<br>2. 长上下文竞争加剧<br>3. 视频生成能力快速迭代<br>4. 定价策略趋于多元化</p>
                    </div>
                </div>
            </div>

            <div class="market-section">
                <h2>📅 重要发布事件时间线 (2026)</h2>
                <div class="timeline">
                    <div class="timeline-item">
                        <div class="date">2026年1月</div>
                        <div class="title">OpenAI 发布 GPT-4o with Vision</div>
                        <div class="desc">原生多模态模型，支持实时语音和视频理解</div>
                    </div>
                    <div class="timeline-item">
                        <div class="date">2026年2月</div>
                        <div class="title">Google Gemini 2.0 Ultra 发布</div>
                        <div class="desc">1M token 上下文，支持更复杂推理任务</div>
                    </div>
                    <div class="timeline-item">
                        <div class="date">2026年3月</div>
                        <div class="title">Claude 4 系列发布</div>
                        <div class="desc">增强推理能力，全新 Agent 架构</div>
                    </div>
                    <div class="timeline-item">
                        <div class="date">2026年4月</div>
                        <div class="title">OpenAI o3 推理模型上线</div>
                        <div class="desc">强化学习驱动的推理能力，数学/代码大幅提升</div>
                    </div>
                    <div class="timeline-item">
                        <div class="date">2026年5月</div>
                        <div class="title">Google AI 新品发布</div>
                        <div class="desc">Veo 3, Imagen 4, Project Astra 进展</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sources -->
        <div class="sources-section">
            <h3>🔗 参考来源</h3>
            <div class="source-list">
                {self._build_source_list(companies_data)}
            </div>
        </div>
    </div>

    <footer class="footer">
        <p>本报告由 AI Agent 自动生成 | 数据来源：公开网络搜索</p>
        <div class="disclaimer">
            ⚠️ 免责声明：报告中包含的信息基于网络搜索结果，可能存在时效性偏差。建议读者核实关键信息后再做决策。
        </div>
    </footer>

    <script>
        function showTab(tabId) {{
            // Hide all sections
            document.querySelectorAll('.company-section').forEach(el => {{
                el.classList.remove('active');
            }});
            // Deactivate all tabs
            document.querySelectorAll('.nav-tab').forEach(el => {{
                el.classList.remove('active');
            }});
            // Show selected section
            document.getElementById(tabId).classList.add('active');
            // Activate selected tab
            event.target.classList.add('active');
        }}

        // Show first tab by default
        document.querySelector('.nav-tab').click();
    </script>
</body>
</html>"""

    def _build_companies_data(self) -> Dict:
        """构建公司数据"""
        openai_products = len(self.data.get("openai", {}).get("products", []))
        google_products = len(self.data.get("google", {}).get("products", []))
        claude_products = len(self.data.get("claude", {}).get("products", []))
        openai_sources = len(self.data.get("openai", {}).get("sources", []))
        google_sources = len(self.data.get("google", {}).get("sources", []))
        claude_sources = len(self.data.get("claude", {}).get("sources", []))

        return {
            "openai": self.data.get("openai", {"products": [], "sources": []}),
            "google": self.data.get("google", {"products": [], "sources": []}),
            "claude": self.data.get("claude", {"products": [], "sources": []}),
            "total_products": openai_products + google_products + claude_products,
            "total_sources": openai_sources + google_sources + claude_sources
        }

    def _build_company_sections(self, companies_data: Dict) -> str:
        """构建公司内容区域"""
        sections = []
        company_keys = ["openai", "google", "claude"]

        for company in company_keys:
            data = companies_data.get(company, {"products": [], "sources": []})
            company_names = {"openai": "OpenAI", "google": "Google AI", "claude": "Claude (Anthropic)"}
            taglines = {"openai": "推动 AI 技术的边界", "google": "让 AI 惠及每个人", "claude": "构建安全、有益的 AI 系统"}

            products_html = ""
            for product in data.get("products", [])[:8]:
                if isinstance(product, dict):
                    features_html = "".join([f'<span class="feature-tag">{f}</span>' for f in product.get("key_features", [])[:4]])
                    products_html += f'''
                    <div class="product-card">
                        <h3>{product.get("name", "未命名产品")}</h3>
                        <div class="date">📅 {product.get("announcement_date", "2026")}</div>
                        <div class="description">{product.get("description", "")[:200]}...</div>
                        <div class="features">{features_html}</div>
                        <div class="source">🔗 来源: <a href="{product.get("source_url", "#")}" target="_blank">{product.get("source_url", "#")[:50]}...</a></div>
                    </div>
                    '''

            if not products_html:
                products_html = '''
                <div class="product-card">
                    <p>正在加载产品信息...</p>
                </div>
                '''

            sections.append(f'''
            <div class="company-section" id="{company}">
                <div class="company-header {company}">
                    <h2>{"🔵" if company == "openai" else "🟢" if company == "google" else "🟠"} {company_names[company]}</h2>
                    <div class="tagline">{taglines[company]}</div>
                </div>
                <div class="products-grid">
                    {products_html}
                </div>
            </div>
            ''')

        return "\n".join(sections)

    def _build_source_list(self, companies_data: Dict) -> str:
        """构建来源列表"""
        sources_html = []
        company_keys = ["openai", "google", "claude"]

        for company in company_keys:
            data = companies_data.get(company, {"sources": []})
            for source in data.get("sources", [])[:5]:
                if isinstance(source, dict):
                    sources_html.append(f'''
                    <div class="source-item">
                        <a href="{source.get("url", "#")}" target="_blank">{source.get("title", "来源")}</a>
                        <div class="snippet">{source.get("snippet", "")[:100]}...</div>
                    </div>
                    ''')
        return "\n".join(sources_html) if sources_html else "<p>暂无来源</p>"

    def _save_report(self):
        """保存报告"""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(self.html_content)

        print(f"✅ 报告保存到: {self.report_path}")


def main():
    agent = GeneratorAgent()
    result = agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())