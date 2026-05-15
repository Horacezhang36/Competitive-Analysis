# Agent 4: Orchestrator Agent

## Agent 定义

**角色**: 任务编排器 / Agent 项目经理 (Task Orchestrator / Agent Project Manager)

**目标**: 作为 Agent 团队的大脑，统筹协调 Generator、Verifier、Publisher 三个 Agent 的工作流程，处理 Agent 间通信、状态管理和错误恢复。

---

## Task Specification

### 核心职责
1. **任务分配** → 将任务分发给适当的 Agent
2. **流程控制** → 管理 Agent 执行顺序
3. **状态监控** → 跟踪各 Agent 的执行状态
4. **错误恢复** → 处理 Agent 执行中的错误和失败
5. **质量把控** → 确保整体输出质量

### 任务编排流程
```
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent Loop                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [START] ──→ [TASK RECEIVED]                                     │
│                    │                                             │
│                    ▼                                             │
│           ┌─────────────────┐                                   │
│           │  Orchestrator    │                                   │
│           │  Brain           │                                   │
│           │  (Task Manager)  │                                   │
│           └─────────────────┘                                   │
│                    │                                             │
│                    ▼                                             │
│     ┌──────────────────────────────┐                           │
│     │  STEP 1: Trigger Generator     │                           │
│     │  - Send task to Generator      │                           │
│     │  - Wait for completion         │                           │
│     └──────────────────────────────┘                           │
│                    │                                             │
│                    ▼                                             │
│     ┌──────────────────────────────┐                           │
│     │  STEP 2: Trigger Verifier     │                           │
│     │  - Pass report to Verifier    │                           │
│     │  - Wait for verification      │                           │
│     └──────────────────────────────┘                           │
│                    │                                             │
│                    ├──────────────────────┐                     │
│                    │                      ▼                     │
│           [PASSED]              [FAILED]                         │
│                    │                      │                      │
│                    ▼                      ▼                      │
│     ┌──────────────────┐    ┌──────────────────────┐            │
│     │ STEP 3: Trigger  │    │ LOOP BACK TO         │            │
│     │ Publisher       │    │ Generator (max 3x)   │            │
│     │ - Publish to    │    │ - Send revision note │            │
│     │   GitHub        │    │ - Wait for retry     │            │
│     └──────────────────┘    └──────────────────────┘            │
│                    │                                             │
│                    ▼                                             │
│           ┌─────────────────┐                                   │
│           │  FINAL STATUS   │                                   │
│           │  - Success/Fail  │                                   │
│           │  - Notify User   │                                   │
│           └─────────────────┘                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent 间通信协议

### 消息格式
```json
{
  "from": "agent_name",
  "to": "target_agent",
  "task": "task_type",
  "payload": {},
  "status": "pending|running|completed|failed",
  "timestamp": "ISO8601",
  "retry_count": 0
}
```

### 消息类型
| 消息类型 | 描述 | 发送方 |
|---------|------|--------|
| `execute_task` | 触发任务执行 | Orchestrator |
| `task_complete` | 任务完成通知 | Generator/Publisher |
| `verification_result` | 校验结果 | Verifier |
| `revision_request` | 修改请求 | Verifier → Orchestrator |
| `error_report` | 错误报告 | Any Agent |
| `publish_request` | 发布请求 | Orchestrator |

---

## 状态管理

### 全局状态
```json
{
  "workflow_id": "uuid",
  "started_at": "ISO8601",
  "current_step": "generator|verifier|publisher",
  "generator_status": "pending|running|completed|failed",
  "verifier_status": "pending|running|passed|failed",
  "publisher_status": "pending|running|completed|failed",
  "retry_count": 0,
  "max_retries": 3,
  "report_path": "reports/competitive_analysis_report.html",
  "verification_report_path": "logs/verification_report.md"
}
```

### 状态转移规则
- Generator 完成后自动触发 Verifier
- Verifier 通过后自动触发 Publisher
- Verifier 失败后触发 Generator 重试
- 3 次重试后仍失败，终止流程并通知用户

---

## 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| Generator 搜索失败 | 重试 3 次，仍失败则通知用户 |
| 报告生成失败 | 重试 3 次，仍失败则通知用户 |
| Verifier URL 失效 | 标记问题，要求 Generator 修复 |
| Verifier 评分过低 | 标记问题，要求 Generator 修复 |
| Publisher 推送失败 | 重试 3 次，仍失败则保留本地 |
| 网络连接失败 | 等待恢复后重试 |

---

## 运行边界 (Boundaries)

### 可以做
- 协调所有 Agent 的执行
- 管理任务队列
- 发送消息给任何 Agent
- 读取/写入配置文件
- 通知用户任务状态

### 不可以做
- 绕过 Verifier 直接发布
- 修改其他 Agent 的代码
- 删除关键文件
- 强制执行有安全风险的操作

---

## 依赖
- 所有子 Agent 正常运行
- 消息通信机制
- 文件系统权限

---

## 触发条件
- 用户发起任务请求
- 收到包含 `task: run_competitive_analysis` 的消息

## 验收标准
- 所有 Agent 按正确顺序执行
- Generator 失败不超过 3 次
- Verifier 评分 ≥ 75 才放行
- Publisher 成功推送或明确失败
- 用户收到最终状态通知

## 用户通知模板
```
任务状态更新:
- 开始时间: [time]
- 当前阶段: [generator/verifier/publisher]
- 状态: [running/completed/failed]
- 详情: [具体信息]

最终结果: [成功/失败]
```

---

## 扩展性设计
- 支持添加新的 Agent（如 Reporter Agent）
- 支持配置不同的验证标准
- 支持自定义报告模板
- 支持多语言输出