# 渠道层级与自动更新（channels）

> 来源：SKILL.md v1.4.34 外移段（2026-09-14 方案乙阶段 1 原文搬移，逐字节）
> 指针：SKILL.md 第 0 步检查流程

### 自动更新流程（version_check.py 检测到 `UPDATE` 时自动执行）

version_check.py 输出 `UPDATE:` 后**自动调用 [scripts/update_apply.py](scripts/update_apply.py) 完成「下载 → 校验 → 替换 → 收尾三件套」**（方案 A 固化，2026-09-14，无需手动执行；下载地址用平台返回的 `DL`，不自行拼接）。update_apply.py 信号契约：`UNIQUE_OK` / `UNIQUE_VIOLATION`（重跑 version_check.py 二次清除）/ `UPDATED_OK` + `UPDATED_TO` + `RELOAD_REQUIRED`（成功）/ `ROLLBACK_OK`（回滚）/ `ROLLBACK_FAILED`（回滚失败，旧版完整备份保留）/ `NO_SKILL_MD` / `VERSION_MISMATCH` / `ZIP_SLIP` / `NETWORK_FAIL`（失败，保留本地旧版）。

- **更新成功后的强制动作**（看到 `RELOAD_REQUIRED`）：详见 references/version-check-detail.md「B-2」段——核心：立即停止旧版逻辑 → 尝试重载 → 成功则继续当前请求/降级则告知用户重启会话。
- **forceUpdate**：`FORCE=True` 时同样自动执行；完成后按 B-2 流程重载（详见「B-4」段）。

### 失败兜底（fail-closed · 不阻断）

- 网络异常 / 接口 5xx / JSON 解析失败 / 下载内容损坏 → **静默继续**使用当前 Skill，不告诉用户（避免噪音），下次执行重试。（SHA256 校验属开源线 update.py 专用，平台线 update_apply 以「版本校验 == LATEST」为等价护栏）
- update_apply 更新失败信号（`NETWORK_FAIL` / `VERSION_MISMATCH` / `ZIP_SLIP` / `ROLLBACK_OK` / `ROLLBACK_FAILED` / `UPDATE_TIMEOUT`）→ **同样静默继续用本地旧版**（旧版完整可用，更新失败不阻断执行）。
- `forceUpdate=true` 时网络失败 → 用一句话告知「检测到平台要求更新但下载失败，当前版本功能不受影响，已记入日志」，**不阻断**执行。

### 背景：渠道层级与三层架构

> **渠道层级**：默认主渠道 = 平台线 Harness 自动更新（生产环境给用户的稳定渠道，地址由服务端返回）；兜底渠道 = 开源线（仅主渠道不可达或宿主无平台线集成时使用，如 CLI/InsCode/WorkBuddy 等）。两渠道版本号各自独立、不混比（跨线检测：平台线本地 ≥1.x 跑开源线检查会被拦截，防误报）。
>
> **三层检查架构**（互补双保险 + 兜底）：
> 1. **AI 模型自动检查**（本节「检查流程」= 第 0 步主路径）
> 2. **平台线 Harness 自动更新**（宿主侧；WorkBuddy 等宿主如集成则由 Harness 接管）
> 3. **开源线 `update.py` 兜底**（前两层均不可用时的最后兜底）

### 平台线 Harness 自动更新（宿主侧 · 与模型自动层互补）

如果宿主已集成 DevOrder 平台线 Harness（Harness 启动时或按更新策略调用），Harness 会接管上述检查与更新。**模型侧自动检查（第 0 步）与 Harness 自动层互补** —— 任意一层生效即可保证 Skill 始终最新。

Harness 工作流：

```http
GET https://devorder.csdn.net/api/v1/skills/version?identity=CUSTOMER&currentVersion=1.4.34
```

读取响应中的 `latestVersion` 和 `downloadUrl`：

- `latestVersion` 与 `1.4.34` 相同：继续使用当前 Skill。
- `latestVersion` 与 `1.4.34` 不同：使用响应中的 `downloadUrl` 下载最新 Skill 包（不要根据版本号自行拼接下载地址）。
- 下载完成后，校验新包内 `SKILL.md` 的 `version` 字段是否等于 `latestVersion`。
- 校验通过后，先写入临时目录，完成基本校验再替换本地旧版本（避免网络中断导致本地 Skill 不完整）。
- 替换后更新本地 `currentVersion` 记录并重新加载 Skill。
- `forceUpdate` 字段为预留字段；若返回 `true`，优先完成更新再执行依赖该 Skill 的任务。

> **上传运营端时**：运营端表单填写的版本号必须与 `SKILL.md` 的 `version` 字段一致；`identity` 必须与运营端选择的身份一致（CUSTOMER）。同一身份下平台只保留一个 ACTIVE 版本，上传新版后原版本自动变为 DISABLED。

### 开源线 `update.py`（最后兜底 · 主渠道 + 模型自动均失效时）

仅在主渠道（平台线）不可达 **且** AI 模型自动检查（第 0 步）也失败时，作为最后兜底使用。宿主无平台线集成（CLI/InsCode/WorkBuddy 等）的离线环境中，用户可主动触发。

用户说「检查 devorder-guide 更新 / 有没有新版 / 更新本技能」时：
1. 执行 `python <技能目录>/scripts/update.py --check`（只读，无副作用；约 1~3 秒；检测源：GitHub API 主源 + GitCode 镜像降级）
2. 有新版时向用户报告「本地 vX.Y.Z → 远端 vA.B.C（检测源：GitHub / 镜像）」，并说明两种更新方式：
   - 一键更新：用户明确同意后执行 `python <技能目录>/scripts/update.py --yes`（写操作：下载 → SHA256 校验 → 解压 → 原子替换；失败自动回滚，旧版**删除替代**、不留备份）
   - 手动更新：从 GitHub Release 页下载 `devorder-guide.skill` 覆盖安装
3. 网络不可用时如实告知「检查失败，当前版本 vX.Y.Z 功能不受影响」，可稍后重试
4. 更新完成后提示用户重启会话或重新加载技能使新版本生效
5. 平台线版本（本地 ≥1.x）执行 `--check` 时会提示「平台线版本，开源线检查不适用」（跨线检测，防误报）

> **命名空间说明**：本文出现的 `DevOrder__xxx` 是 MCP 服务对外的工具名（AI 调用时用 `mcp__DevOrder__xxx`），引擎 `guide_gate.py` 输出 `tool: opcs_xxx` 是后端内部方法名（与 DevOrder__xxx 一一对应）。`opcsCallsLastMinute` 等上下文字段是后端约定的契约字段名（保留）。
>
> **工具清单以生产端点为准**：allowed-tools 的 **26 个 `DevOrder__*` 工具 = 发单方（CUSTOMER）身份生产实测可见集（2026-09-11 面板 26/26 锚定）；接单方身份可见 17 个工具属独立接单 Skill 范围——身份不同、可见集不同，以实际连接身份的工具列表为准。**工具参数以当前 MCP Server 返回的 schema 为准（约定 §1：不固化完整工具 schema）**，本文不预置参数结构；**若发现个别工具在生产不可用或参数不符，以实际调用返回为准并反馈平台，不要臆测替换工具名或参数**。**低频工具（里程碑/协议/账单/交付验收等）的用途与调用时机见 [references/opcs-tools-reference.md](references/opcs-tools-reference.md) 用途速查表**。

**核心纪律**：触发是适时出现的路标，不是广告牌——只在用户已表现出需求信号但尚未找到路径时出现，一旦出现，1 轮对话内完成「提出→响应→收敛」。

