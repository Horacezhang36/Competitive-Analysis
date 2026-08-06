# AgentKit Runtime 持续集成与持续交付

验证时间：2026-08-06  
本次目标：把 AgentKit Runtime 的持续交付链路真实跑通，并沉淀为 GitHub 可复用示例。

## 1. 核心概念

AgentKit Runtime 持续交付不是简单的“重新部署一次”。它把代码、镜像、Runtime 资源、版本、流量入口和回滚能力串成一条可审计的工程链路。

| 阶段 | 作用 | 对应动作 |
|---|---|---|
| 持续集成 CI | 每次代码变化后自动检查代码是否可构建、可测试、可交付 | lint、单元测试、导入测试、构建镜像 |
| 持续交付 CD | 将通过质量门禁的产物交付到可发布状态 | 创建 Runtime、更新待发布版本、生成发布证据 |
| 持续部署 Deployment | 将某个版本切换到线上入口 | `agentkit runtime release` |
| 回滚 Rollback | 当新版本异常时切回历史版本 | `agentkit runtime release --version-number N` |

对 AgentKit Runtime 来说，CI/CD 的关键对象是“Runtime 版本”，而不是某个本地 Python 文件。代码必须先构建成镜像，再通过 Runtime 创建、更新、发布、回滚进入线上流量。

## 2. 持续集成原理

持续集成关注“这个变更是否具备交付资格”。在本仓库中，CI 至少应该检查四类问题：

1. 代码能否被 Python 解释器正确导入。
2. Agent 或服务入口是否存在，例如 `app.py` 是否能暴露 FastAPI 应用。
3. 镜像能否被 AgentKit CLI 构建。
4. 自动化脚本和工作流路径是否正确。

本次修复的典型 CI 问题包括：

- GitHub Actions 中 verifier 的报告路径写错，`agents/verifier` 下的 `../reports` 实际不会指向仓库根目录的 `reports`。
- 发布步骤写入 `docs/latest.md` 前没有创建 `docs` 目录。
- `sync_to_github.sh` 的变更检测语句损坏，导致脚本无法可靠判断是否需要提交。
- Orchestrator 直接 `json.loads(stdout)`，但子 Agent 会先打印日志再输出 JSON，导致父流程无法稳定解析状态。

这些问题属于持续集成应该提前发现和阻断的工程问题。

## 3. 持续交付原理

AgentKit Runtime 的持续交付链路可以理解为五个控制点：

| 控制点 | 含义 | 教学重点 |
|---|---|---|
| Build | 将本地代码构建成云端镜像 | 构建成功只代表有可交付产物，不代表线上已更新 |
| CreateRuntime | 创建线上 Runtime 资源 | 绑定镜像、入口、KeyAuth、实例规格、环境变量和运行身份 |
| UpdateRuntime | 提交新配置或新镜像 | 可以形成未发布变更，线上入口不一定变化 |
| ReleaseRuntime | 切换线上版本 | 这是流量入口真正生效的动作 |
| Rollback | 切回历史版本 | 通过指定 `--version-number` 完成 |

最重要的教学结论：

- `update` 不等于线上发布。
- `release` 才是线上入口切换。
- 回滚本质上也是一次 release，只是目标版本是历史版本。
- 容量参数可能更接近 Runtime 资源级配置，不能默认认为版本回滚会恢复全部容量设置。
- Runtime 实例不应该保存关键会话状态；状态应外置到 Session、Memory、Storage 或业务数据库。

## 4. GitHub Actions 配置步骤

进入仓库：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

配置以下 Secrets：

| Secret | 必填 | 用途 |
|---|---|---|
| `VOLCENGINE_ACCESS_KEY` | 是 | 调用 AgentKit / 火山云资源 |
| `VOLCENGINE_SECRET_KEY` | 是 | 调用 AgentKit / 火山云资源 |
| `VOLCENGINE_REGION` | 建议 | 默认使用 `cn-beijing` |
| `AGENTKIT_RUNTIME_ROLE_NAME` | 是 | Runtime 运行身份 RoleName |

仓库不保存 AK/SK、Runtime API Key、GitHub PAT 或其他长期凭据。

建议在仓库设置中检查：

```text
Settings -> Actions -> General -> Workflow permissions
```

如果 workflow 需要回写仓库，例如自动提交报告，选择：

```text
Read and write permissions
```

## 5. 推荐自动化分层

建议把 AgentKit Runtime 自动化拆成三层，不要一开始就让 CI 自动发布生产流量。

| 层级 | 触发方式 | 自动化范围 | 是否直接影响线上 |
|---|---|---|---|
| PR CI | pull request | Python 导入测试、脚本检查、本地 smoke | 否 |
| Build CI | push 或手动触发 | `agentkit build` 生成镜像 | 否 |
| Release CD | 手动触发或审批后触发 | create/update/release/rollback | 是 |

这样设计的原因是：Runtime 发布会影响线上入口，应当保留人工审批或环境保护规则。课程演示可以手动 release，生产环境建议配合 GitHub Environment approval。

## 6. 本仓库新增 workflow

本仓库新增：

```text
.github/workflows/agentkit-runtime-cd.yml
```

该 workflow 的职责是：

1. 拉取代码。
2. 安装 Python 和 AgentKit CLI。
3. 校验必要 Secrets。
4. 执行 `agentkit build --config-file agentkit.yaml`。
5. 输出后续 create/update/release/rollback 指引。

它目前只自动构建，不自动发布线上版本。这样做是为了保留发布审批边界，避免学生或 CI 在无意中切换 Runtime 流量。

## 7. 本地手动跑通步骤

进入示例目录：

```bash
cd /Users/bytedance/Documents/VeADK项目/Competitive-Analysis/agentkit-runtime-cd
```

配置环境变量：

```bash
export VOLCENGINE_REGION="cn-beijing"
```

配置 AgentKit 地域：

```bash
export VOLCENGINE_AGENTKIT_REGION="cn-beijing"
```

构建镜像：

```bash
agentkit build --config-file agentkit.yaml
```

从 `agentkit.yaml` 中读取构建后的镜像地址，或在构建日志中复制 `Build completed:` 后面的镜像地址：

```bash
export AGENTKIT_IMAGE_URL="agentkit-platform-xxxx-cn-beijing.cr.volces.com/agentkit/agentkit-runtime-cd:yyyymmddhhmmss"
```

配置 Runtime 运行身份：

```bash
export AGENTKIT_RUNTIME_ROLE_NAME="AgentKit_Runtime_Default_ServiceRole_xxxxx"
```

生成 v1 创建参数：

```bash
python3 scripts/render_runtime_payload.py create-v1 --name "agentkit-runtime-cd-demo" --image "$AGENTKIT_IMAGE_URL" --role-name "$AGENTKIT_RUNTIME_ROLE_NAME" > /tmp/runtime-create-v1.json
```

创建 Runtime：

```bash
agentkit runtime create --name "agentkit-runtime-cd-demo" --role-name "$AGENTKIT_RUNTIME_ROLE_NAME" --artifact-type image --artifact-url "$AGENTKIT_IMAGE_URL" --json "$(cat /tmp/runtime-create-v1.json)" --region cn-beijing
```

保存返回的 Runtime ID：

```bash
export RUNTIME_ID="r-xxxxxxxxxxxxxxxxxxxx"
```

查看 Runtime：

```bash
agentkit runtime get --runtime-id "$RUNTIME_ID" --region cn-beijing --output json
```

生成 v2 未发布更新参数：

```bash
python3 scripts/render_runtime_payload.py update-v2-unreleased --runtime-id "$RUNTIME_ID" --image "$AGENTKIT_IMAGE_URL" > /tmp/runtime-update-v2-unreleased.json
```

提交 v2 但不发布，观察控制面进入 `UnReleased`，同时线上 Endpoint 仍返回 v1：

```bash
agentkit runtime update --runtime-id "$RUNTIME_ID" --json "$(cat /tmp/runtime-update-v2-unreleased.json)" --region cn-beijing
```

发布当前待发布版本：

```bash
agentkit runtime release --runtime-id "$RUNTIME_ID" --region cn-beijing
```

生成 v3 扩容并立即发布参数：

```bash
python3 scripts/render_runtime_payload.py update-v3-release --runtime-id "$RUNTIME_ID" --image "$AGENTKIT_IMAGE_URL" > /tmp/runtime-update-v3-release.json
```

发布 v3 扩容版本，将 `MaxInstance` 从 2 提高到 3：

```bash
agentkit runtime update --runtime-id "$RUNTIME_ID" --json "$(cat /tmp/runtime-update-v3-release.json)" --region cn-beijing
```

回滚到 v1：

```bash
agentkit runtime release --runtime-id "$RUNTIME_ID" --version-number 1 --region cn-beijing
```

调用线上 Endpoint：

```bash
python3 scripts/probe_runtime.py
```

并发探针：

```bash
python3 scripts/loadtest_sleep.py --concurrency 60 --seconds 5 --out loadtest.json
```

## 8. 本次实测资源

| 项目 | 值 |
|---|---|
| Runtime ID | `r-yes99n1p1c5agefdln75` |
| Runtime Name | `codex-runtime-cd-20260806210737` |
| Region | `cn-beijing` |
| Endpoint | `https://s93430gf6rsmb73422ghl.apigateway-cn-beijing.volceapi.com` |
| 当前最终版本 | `1` |
| 当前最终状态 | `Ready` |
| 认证方式 | KeyAuth |

API Key 不写入文档、仓库或日志，只在命令执行时通过环境变量传递。

## 9. 关键验证结果

### v1 创建并调用成功

`/version` 返回：

```json
{
  "version": "v1",
  "release_marker": "COURSE_CD_V1",
  "elasticity_model": "request-level"
}
```

### v2 更新但不发布

控制面返回：

```text
Status=UnReleased
CurrentVersionNumber=1
```

线上 Endpoint 仍返回：

```json
{
  "version": "v1",
  "release_marker": "COURSE_CD_V1"
}
```

说明：更新 Runtime 配置不等于线上生效；必须执行 release，线上入口才切到新版本。

### v2 发布后生效

发布后轮询结果：

```text
status=Ready
version=2
```

线上 Endpoint 返回：

```json
{
  "version": "v2",
  "release_marker": "COURSE_CD_V2_UNRELEASED"
}
```

### v3 扩容发布

发布后轮询结果：

```text
status=Ready
version=3
maxInstance=3
```

线上 Endpoint 返回：

```json
{
  "version": "v3",
  "release_marker": "COURSE_CD_V3_SCALEOUT"
}
```

### 并发探针

60 并发请求 `/sleep?seconds=5`：

```json
{
  "status_counts": {
    "200": 60
  },
  "hostname_counts": {
    "vefaas-kg2exmhs-h8ksk6lhfh-d9q8fl0gluloen65j760": 29,
    "kg2exmhs-h8ksk6lhfh-reserved-5dc4844fdb-m8vbq": 31
  },
  "latency_median": 5.12,
  "latency_p95_approx": 5.302
}
```

说明：本次压测触发了两个实例承载请求，60 个请求全部成功，适合用于解释 Runtime 的请求级弹性。

### 回滚到 v1

执行指定版本发布后：

```text
status=Ready
version=1
maxInstance=3
```

线上 Endpoint 返回：

```json
{
  "version": "v1",
  "release_marker": "COURSE_CD_V1"
}
```

注意：本次回滚后应用版本回到 v1，但 `MaxInstance` 仍保持 3。这说明容量参数可能更接近 Runtime 资源级配置，课程中不要默认承诺版本回滚会恢复全部容量设置。
