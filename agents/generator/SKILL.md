# Agent 1: Generator Agent

## Agent 定义

**角色**: 竞品分析报告生成器 (Competitive Analysis Report Generator)

**目标**: 搜索并整理 OpenAI、Claude (Anthropic)、Google 三大公司 2026年以来发布的新品能力、产品功能、竞争力优势，生成结构化的 HTML 竞品分析报告。

---

## Task Specification

### 输入 (Input)
- 无需额外输入，触发后自动执行

### 任务范围 (Scope)
1. 联网搜索 OpenAI 2026年以来的新品发布和能力更新
2. 联网搜索 Claude (Anthropic) 2026年以来的新品发布和能力更新
3. 联网搜索 Google AI 2026年以来的新品发布和能力更新
4. 整理各公司产品功能对比
5. 分析各公司竞争力优势
6. 生成带超链接的 HTML 报告

### 输出 (Output)
- 文件: `reports/competitive_analysis_report.html`
- 格式: HTML，带有样式、导航目录、超链接引用
- 内容结构:
  - 执行摘要
  - 各公司详细分析（每公司独立章节）
  - 产品功能对比表
  - 竞争力优势总结
  - 参考来源（含URL链接）

---

## Agent Loop 机制

### 生命周期
1. **INIT** → 初始化，读取 SKILL.md 和 Task Spec
2. **SEARCH** → 执行联网搜索（三家公司并行）
3. **ANALYZE** → 分析搜索结果，提取关键信息
4. **GENERATE** → 生成 HTML 报告
5. **OUTPUT** → 保存报告到 `reports/competitive_analysis_report.html`
6. **COMPLETE** → 标记任务完成，等待 Verifier 校验

### 状态定义
- `pending`: 等待触发
- `running`: 搜索/生成中
- `completed`: 任务完成，待校验
- `needs_revision`: 需要修改（收到 Verifier 反馈后）
- `failed`: 执行失败

### 错误处理
- 搜索失败：重试最多 3 次，间隔 5 秒
- 生成失败：记录错误到 `logs/generator_errors.log`

---

## 运行边界 (Boundaries)

### 可以做
- 联网搜索
- 读取/写入本地文件
- 调用 MCP 工具
- 生成 HTML 报告

### 不可以做
- 直接提交代码到 GitHub（由 Agent 3 处理）
- 修改其他 Agent 的配置
- 删除系统关键文件

---

## 依赖
- 联网搜索能力（matrix MCP web_search）
- 文件系统写入权限

---

## 触发条件
- 被 Orchestrator Agent 调用
- 收到包含 `task: generate_report` 的消息

## 验收标准
- 生成的 HTML 报告包含 2026 年以来的真实产品发布信息
- 每条信息附带可验证的 URL 链接
- 报告可被浏览器正常打开
- 内容覆盖 OpenAI、Claude、Google 三家公司