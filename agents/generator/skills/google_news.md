# Skill: Google AI News Fetcher
# 从 Google AI 官方渠道获取最新产品发布信息

## 描述
从 Google AI 官方网站、DeepMind 博客、Gemini API 文档等渠道获取 2026 年以来的新品发布、能力更新、功能特性等信息。

## 数据源
- 主站: https://ai.google
- DeepMind: https://deepmind.google
- Gemini: https://gemini.google.com
- AI Studio: https://aistudio.google.com
- Google Cloud AI: https://cloud.google.com/products/ai
- 博客: https://blog.google/technology/ai/

## 搜索关键词
```
Google Gemini 2026 new features
Google DeepMind 2026 updates
Google AI Agent updates
Google Veo 3 release
Google Imagen 3 announcement
Google Project Mariner
Google AI Ultra subscription
Google AI May 2026
Gemini 2.5 Pro features
```

## 输出格式
```json
{
  "company": "Google AI",
  "products": [
    {
      "name": "产品名称",
      "announcement_date": "发布日期",
      "category": "category_type",
      "description": "详细描述",
      "key_features": ["功能1", "功能2", ...],
      "pricing": "定价信息",
      "use_cases": ["使用场景"],
      "technical_specs": {
        "parameter": "value"
      },
      "source_url": "官方来源链接",
      "competitor_advantages": "竞争优势描述"
    }
  ],
  "overall_analysis": "整体竞争力分析",
  "market_position": "市场定位"
}
```

## 验证规则
- 所有产品必须有官方来源 URL
- 日期必须标注
- 功能描述不少于 50 字