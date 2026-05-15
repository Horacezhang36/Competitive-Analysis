# Agent 3: GitHub Publisher Agent

## Agent 定义

**角色**: GitHub 仓库发布者 (GitHub Repository Publisher)

**目标**: 当 Verifier Agent 校验通过后，将 Generator 和 Verifier 的代码打包并发布到 GitHub 仓库。

**目标仓库**: https://github.com/Horacezhang36/Competitive-Analysis

---

## Task Specification

### 输入 (Input)
- 报告文件: `reports/competitive_analysis_report.html`
- Agent 代码: `agents/` 目录下的所有代码
- 验证通过标记

### 发布流程 (Publish Flow)
1. **PREPARE** → 准备要发布的文件
2. **COMMIT** → 创建 Git 提交
3. **PUSH** → 推送到 GitHub 仓库
4. **CONFIRM** → 确认发布成功

### 发布内容
- `agents/` 目录（完整的 Agent 代码）
- `reports/` 目录（生成的报告）
- `README.md`（项目说明文档）
- `.gitignore`（忽略临时文件）

---

## Agent Loop 机制

### 状态定义
- `pending`: 等待触发
- `preparing`: 准备发布文件
- `committing`: 创建 Git 提交
- `pushing`: 推送到远程
- `completed`: 发布成功
- `failed`: 发布失败

### 错误处理
- 推送失败：保留本地更改，重试最多 3 次
- 冲突处理：尝试 rebase 或合并
- 认证失败：请求用户授权

### Git 操作策略
```
1. git init（如果仓库不存在）
2. git add .
3. git commit -m "Auto-publish: competitive analysis report [date]"
4. git remote add origin [URL]（如果未设置）
5. git push -u origin main
```

---

## 运行边界 (Boundaries)

### 可以做
- 创建 Git 仓库
- 提交和推送代码
- 创建 README 等文档
- 配置 .gitignore

### 不可以做
- 强制推送到 main 分支
- 删除远程仓库内容
- 修改其他 Agent 的配置

---

## 依赖
- Git 工具
- GitHub CLI 工具（gh）
- 网络连接
- 用户授权（如需要）

---

## 触发条件
- Verifier Agent 校验通过后
- 收到包含 `task: publish_to_github` 的消息

## 验收标准
- 代码成功推送到指定仓库
- 仓库包含所有 Agent 代码
- 报告 HTML 文件在仓库中可访问
- 推送操作留下 Git 历史记录

## 用户授权流程
如果需要 GitHub 认证：
1. Agent 3 请求用户提供 token 或登录授权
2. 使用 `gh auth login` 进行认证
3. 缓存认证信息供后续使用