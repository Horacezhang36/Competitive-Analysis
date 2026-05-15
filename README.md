# Competitive Analysis Demo

AI 竞品分析报告自动生成 Multi-Agent 系统

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
├── verifier/      # Agent 2: 内容校验器
├── publisher/     # Agent 3: GitHub 发布器
└── orchestrator/  # Agent 4: 任务编排器
```

## Agent 职责

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| Generator | 联网搜索竞品信息，生成 HTML 报告 | 无 | `reports/competitive_analysis_report.html` |
| Verifier | 校验报告内容准确性，决定是否放行 | 报告文件 | `logs/verification_report.md` |
| Publisher | 将代码和报告发布到 GitHub | 验证通过标记 | GitHub 仓库 |
| Orchestrator | 统筹协调各 Agent 工作流程 | 无 | 工作流状态 |

## 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent Loop                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [START] ──→ [TASK RECEIVED]                                    │
│                    │                                              │
│                    ▼                                              │
│     ┌──────────────────────────────┐                             │
│     │  STEP 1: Trigger Generator   │                             │
│     │  - 联网搜索 OpenAI/Claude/Google                             │
│     │  - 生成 HTML 报告            │                             │
│     └──────────────────────────────┘                             │
│                    │                                              │
│                    ▼                                              │
│     ┌──────────────────────────────┐                             │
│     │  STEP 2: Trigger Verifier    │                             │
│     │  - 事实核查                  │                             │
│     │  - URL 验证                  │                             │
│     │  - 完整性检查                │                             │
│     └──────────────────────────────┘                             │
│                    │                                              │
│           ┌────────┴────────┐                                    │
│      [PASSED]           [FAILED]                                │
│           │                │                                      │
│           ▼                ▼                                      │
│  ┌──────────────┐  ┌──────────────────┐                         │
│  │ STEP 3:      │  │ LOOP BACK TO      │                         │
│  │ Publisher    │  │ Generator (max 3x) │                         │
│  │ - 推送到 GitHub │  │ - 重新搜索/生成    │                         │
│  └──────────────┘  └──────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Loop 机制

### 回退循环 (Rollback Loop)

当 Verifier 校验失败时：

1. **Verifier** 生成详细的问题报告
2. 通过 **Orchestrator** 通知 **Generator**
3. **Generator** 重新执行任务（最多 3 次）
4. 3 次后仍不通过，终止流程并通知用户

### 重试规则

| 问题类型 | 严重度 | 处理方式 |
|---------|--------|---------|
| 产品名称错误 | CRITICAL | 必须修复 |
| 关键事实错误 | CRITICAL | 必须修复 |
| URL 失效 | MAJOR | 应该修复 |
| 关键信息缺失 | MAJOR | 应该修复 |
| 格式问题 | MINOR | 建议修复 |

### 评分标准

| 校验项 | 权重 | 通过条件 |
|--------|------|---------|
| 事实准确性 | 40分 | ≥ 25分 |
| 内容完整性 | 25分 | ≥ 17分 |
| URL 有效性 | 20分 | ≥ 15分 |
| 时效性 | 15分 | ≥ 10分 |
| **总计** | **100分** | **≥ 75分** |

## 技术栈

- Python 3.8+
- Mavis Multi-Agent Framework
- Matrix MCP (联网搜索)
- Git/GitHub CLI

## 快速开始

### 方式一：使用启动脚本

```bash
# 进入项目目录
cd Competitive_Analysis_demo

# 添加执行权限
chmod +x run.sh

# 运行
./run.sh
```

### 方式二：直接运行 Orchestrator

```bash
cd Competitive_Analysis_demo
python3 agents/orchestrator/orchestrator_agent.py
```

### 方式三：单独运行各 Agent

```bash
# 1. 生成报告
python3 agents/generator/generator_agent.py

# 2. 校验报告
python3 agents/verifier/verifier_agent.py --report reports/competitive_analysis_report.html

# 3. 发布到 GitHub（需要验证通过）
python3 agents/publisher/publisher_agent.py --verified
```

## 目录结构

```
Competitive_Analysis_demo/
├── agents/                    # Agent 代码目录
│   ├── generator/
│   │   ├── SKILL.md          # Agent 定义文档
│   │   └── generator_agent.py # 实现代码
│   ├── verifier/
│   │   ├── SKILL.md
│   │   └── verifier_agent.py
│   ├── publisher/
│   │   ├── SKILL.md
│   │   └── publisher_agent.py
│   └── orchestrator/
│       ├── SKILL.md
│       └── orchestrator_agent.py
├── reports/                    # 生成的报告
│   └── competitive_analysis_report.html
├── logs/                       # 日志文件
│   ├── verification_report.md  # 校验报告
│   ├── workflow_state.json    # 工作流状态
│   └── orchestrator.log       # 执行日志
├── config.ini                  # 配置文件
├── run.sh                      # 启动脚本
└── README.md                   # 本文件
```

## 配置文件说明

`config.ini` 中可以调整以下参数：

```ini
[verifier]
passing_score = 75      # 通过分数（默认 75）
url_validity_threshold = 0.8  # URL 有效率阈值

[publisher]
repo_url = https://github.com/Horacezhang36/Competitive-Analysis  # 目标仓库

[agents]
max_retries = 3         # 最大重试次数
timeout_seconds = 300   # 超时时间（秒）
```

## 常见问题

### Q: GitHub 推送需要认证怎么办？

A: 有以下几种方式：
1. 运行 `gh auth login` 进行交互式登录
2. 设置 `GITHUB_TOKEN` 环境变量
3. 配置 SSH 密钥

### Q: 报告没有内容怎么办？

A: 检查：
1. 网络连接是否正常
2. Matrix MCP 是否可用
3. 查看 `logs/generator_errors.log` 获取详细错误

### Q: Verifier 一直失败怎么办？

A: 检查：
1. 报告是否包含真实的产品信息
2. URL 链接是否有效
3. 内容是否为 2026 年相关信息
4. 查看 `logs/verification_report.md` 了解具体问题

## License

MIT License

---

*本项目由 Mavis Multi-Agent Framework 自动生成*