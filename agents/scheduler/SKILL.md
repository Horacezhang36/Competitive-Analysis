# Agent 5: Scheduler Agent

## Agent 定义

**角色**: 定时任务调度器 + 新品检测器

**目标**: 
1. 每天 8:00 扫描 OpenAI、Google AI、Claude 官方渠道
2. 检测是否有新品发布或重大更新
3. 如果检测到新品，触发整个 Multi-Agent 工作流
4. 最终将 HTML 产物发布到 `competitive-analysis-output` 子目录

---

## Task Specification

### 触发条件
- 定时触发（每天 8:00 UTC，即北京时间 16:00）
- 或手动触发

### 检测流程
```
┌─────────────────────────────────────────────────────────────┐
│  Scheduler Agent                                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 扫描官方渠道                                             │
│     - OpenAI Blog: https://openai.com/blog                 │
│     - Google AI Blog: https://blog.google/technology/ai/  │
│     - Anthropic News: https://www.anthropic.com/news       │
│                                                              │
│  2. 检测新品发布                                             │
│     - 解析 RSS 或爬取最新页面                                │
│     - 比对上次扫描时间                                       │
│     - 识别关键词：new, release, announce, launch             │
│                                                              │
│  3. 决策逻辑                                                 │
│     - 有新品 → 触发 Orchestrator → 生成报告 → CI/CD        │
│     - 无新品 → 静默退出，记录日志                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 输出
- 扫描日志: `logs/scheduler.log`
- 检测报告: `logs/latest_detection.md`
- 触发状态: `logs/trigger_status.json`

---

## Agent Loop 机制

### 执行状态
- `idle`: 等待触发
- `scanning`: 正在扫描
- `detecting`: 检测新品
- `triggering`: 触发工作流
- `completed`: 完成
- `failed`: 失败

### 循环流程
1. **SCAN** → 扫描三个公司官方渠道
2. **COMPARE** → 与上次记录比对
3. **DECIDE** → 决定是否触发
4. **TRIGGER** → 如需触发，启动 Orchestrator
5. **REPORT** → 记录执行状态

---

## 运行边界

### 可以做
- 读取上次扫描记录
- 发送 HTTP 请求获取官方信息
- 写入扫描日志
- 触发 Orchestrator Agent

### 不可以做
- 修改其他 Agent 代码
- 删除系统文件
- 绕过新品检测直接触发

---

## 依赖
- 定时任务配置（crontab 或 GitHub Actions）
- 网络连接
- 文件系统读写权限