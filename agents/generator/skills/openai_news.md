# Skill: OpenAI News Fetcher
# 从 OpenAI 官方渠道获取最新产品发布信息

## 描述
从 OpenAI 官方网站、博客、API 文档等渠道获取 2026 年以来的新品发布、能力更新、功能特性等信息。

## 数据源
- 主站: https://openai.com
- 博客: https://openai.com/blog
- API 文档: https://platform.openai.com/docs
- 新闻: https://openai.com/news/
- 研究: https://openai.com/research

## 搜索关键词
```
OpenAI 2026 new features
OpenAI GPT-5 release
OpenAI o3 announcement
OpenAI Operator features
OpenAI Deep Research updates
OpenAI API new capabilities
OpenAI products May 2026
```

## 输出格式
```json
{
  "company": "OpenAI",
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