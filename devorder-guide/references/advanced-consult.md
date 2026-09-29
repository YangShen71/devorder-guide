# 进阶操作与辅助能力（advanced-consult）

> 来源：SKILL.md v1.4.20 第 4 步外移段（2026-09-14 方案乙阶段 1 原文搬移，逐字节）
> 指针：SKILL.md 第 4 步主路径

**跨平台/会话中断恢复**（进阶）：若用户中途切换 AI 工具（如 WorkBuddy → Claude）或会话中断，可用 `DevOrder__get_advisor_session`（必填 `sessionId`）拉取会话快照（`{phase, facts, ...}`，**仅转达返回中实际存在的字段，`requirementVersion` 等未返回的字段不得假设必有或编造**），带着拉回的状态继续 consult 多轮——**跨平台体验不丢事实**。
**draft_plan → plan_document 展开**（进阶）：若需完整结构化文档（详化阶段任务、添加交付物规格、补充合同要点），在 `DevOrder__draft_plan` 返回 `draftHash` 后跟调 `DevOrder__plan_document`（必填 `sessionId` + `planVersion` + `draftHash`：`^[a-f0-9]{64}$`），**先 draft_plan 后 plan_document** 不要反序。
**draft_plan 前置「信息齐后补强信号轮」**：当 `facts.还需了解=[]` 信息已齐时，**必须读取 [references/consult-flow-detail.md](references/consult-flow-detail.md) 获取强信号词分级 + 正确工作流 + 服务端提示词差异**。核心规则：信息已齐时用强信号词（`发布订单`/`确认发布`），信息未齐时强信号词无效。
**用户中间改需求 → revise_order_draft**（进阶）：用户在 draft_plan/publish_plan 之间反悔改需求（"预算改 5 万"、"目标人群换 30 岁以上"等），调 `DevOrder__revise_order_draft`（必填 `sessionId` + `planVersion` + `draftHash` + `expectedRevision` + `expectedOrderDraftHash` + `mode`：`UPDATE` / `RECONCILE_TASK_TYPES` / `REGENERATE_MODULE`）——**不要重新走完整 consult 流**，避免事实累积被打断。
**publish_plan 失败重试 → retry_publish**（进阶）：`DevOrder__publish_plan` 失败时（5xx、网络中断、参数不一致），用 `DevOrder__retry_publish` 重试（schema 与 publish_plan 完全相同，含 `draftHash` + `orderDraftHash` **双重幂等键**）——避免重复发单。
**资质前置检查（辅助能力）**：在调用 `DevOrder__create_order` 或 `DevOrder__publish_plan` 之前，先调 `DevOrder__get_my_qualification` 读取 `permissions.canCreateOrder`——若为 false，告知用户「当前账号未开通发单权限，请先完善资质或到 DevOrder 网页端申请」。避免硬性 403 错误体验。
**认证资质展示（辅助能力）**：调 `DevOrder__list_my_certification_tags` 读取 `heldTags`（已持有标签如「金牌合作伙伴」「行业专家」等）——在对话中告知用户"你当前是『XX』资质，可申请更多标签"，或筛选接单方时作为筛选条件。
**接单方筛选（辅助能力）**：发单方想定向找接单方时（如"只要金牌合作伙伴 + 具备 React 技能 + 团队"），调 `DevOrder__search_qualified_contractors`，参数按需组合（`certificationTagCodes` + `skills` + `contractorType`），分页默认 10 条。结果可转达为"找到 5 个符合条件的接单方……"。
**当事方订单详情（辅助能力）**：发单方查自己订单的私有字段（联系方式、付款信息等），用 `DevOrder__get_my_order_detail`（含 `onlyVisibleToRoles` 私有段）；公开订单详情用 `DevOrder__get_order_detail`——**两者区别**：前者需要当事方身份，后者任何角色可查脱敏版。
**老手直发分支**：用户**已经明确知道要买什么**（标题/品类/预算齐全）时，可直接用 `DevOrder__create_order`；但用户只是说「我要发单/想做推广」等模糊诉求时**不要用 create_order**——先调 consult 让顾问梳理；三要素（目标人群/量级或预算）不全时服务端会自动把已有信息交给顾问并返回顾问的第一轮追问——此时照常原样转达即可（无需手动重试 create_order，也**不要用编造的值重试**）。
**当 DevOrder MCP 返回错误码时，读取 [references/opcs-errors.md](references/opcs-errors.md) 做错误码兜底**：4xx → 对话内继续（401 告知登录/403 告知角色/404 告知刷新）；5xx/L2 类（L2_NOT_CONFIGURED/L2_TIMEOUT/L2_UNREACHABLE）→ 告知回 Web 端 /client；429 → 静默 60 秒；NEED_CONSULT → 转达顾问追问。所有兜底话术 ≤80 字、含退路、过 check_copy。

