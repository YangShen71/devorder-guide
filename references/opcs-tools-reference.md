# DevOrder MCP 工具参考

> **配套文件**：SKILL.md frontmatter（allowed-tools 已扩展至 26 工具，命名空间 DevOrder__*）
> **约定纪律（§1）**：本文**不固化工具参数 schema**——工具参数以当前 MCP Server 返回的 schema 为准；`allowed-tools` 只列工具名（白名单），不列参数结构。调用时参数名/类型/必填/默认值一律以 MCP 服务端实时返回的 schema 为准，本文不预置参数表。
> **匹配原则**：方法名与 MCP 服务定义 100% 一致；参数细节不在此固化（防 schema 漂移后本文误导）。

---

## 一、26 工具白名单（分类）

| 类别 | 工具 | 数量 |
|---|---|---|
| **顾问流（核心）** | consult, draft_plan, publish_plan | 3 |
| **顾问流（进阶）** | get_advisor_session, revise_order_draft, retry_publish, plan_document | 4 |
| **订单直建（兜底）** | create_order | 1 |
| **订单管理（基础）** | get_my_orders, get_order_detail, list_orders, list_bids, select_bid | 5 |
| **订单管理（进阶）** | get_my_order_detail | 1 |
| **里程碑管理** | add_milestone, configure_milestones, delete_milestone, update_milestone, list_milestones | 5 |
| **协议与账单** | draft_agreement, get_agreement, review_deliverable, get_bill | 4 |
| **资质认证** | get_my_qualification, list_my_certification_tags | 2 |
| **接单方搜索** | search_qualified_contractors | 1 |
| **合计** | — | **26** |

---

## 二、工具用途速查（调用时机与语义，非参数 schema）

> 参数结构以 MCP 服务端实时 schema 为准；下表仅说明「何时用、做什么、关键语义」。

| 工具 | 用途 | 关键语义 / 调用时机 |
|---|---|---|
| `consult` | 顾问梳理需求（发单主路径） | 用户同意后首调；text=用户原话；多轮续接带 sessionId |
| `draft_plan` | 生成正式方案（分项+刊例报价） | phase=ready 后调用；超时原样重试（服务端已缓存） |
| `publish_plan` | 建单发布（1 母单+N 子单） | 用户明确「发布/确认」后；含双重幂等键防重复建单 |
| `get_advisor_session` | 跨平台/断点恢复顾问会话 | 按 sessionId 拉快照，只转达实际返回字段 |
| `revise_order_draft` | 用户中途改需求，局部更新草稿 | draft_plan/publish_plan 之间；不重走完整 consult 流 |
| `retry_publish` | publish_plan 失败后幂等重试 | 5xx/网络中断/参数不一致时；与 publish_plan 同构 |
| `plan_document` | 展开完整结构化文档 | 先 draft_plan 后 plan_document，不反序 |
| `create_order` | 老手直发（三要素齐全时） | 标题/品类/预算齐全才用；模糊诉求先 consult |
| `get_my_orders` | 查我的订单列表 | 只读 |
| `get_order_detail` | 公开订单详情（脱敏版） | 任何角色可查 |
| `get_my_order_detail` | 当事方订单详情（含私有字段） | 当事方身份；非当事方 404 |
| `list_orders` / `list_bids` / `select_bid` | 订单广场/竞标/中标 | 接单路径 |
| `add_milestone` 等 5 工具 | 里程碑增删改查 | 建单后配置 |
| `draft_agreement` / `get_agreement` / `review_deliverable` / `get_bill` | 协议/交付/账单 | 交易闭环 |
| `get_my_qualification` | 资质与权限前置检查 | 写操作前查 canCreateOrder/canBidOrder |
| `list_my_certification_tags` | 认证标签 | 资质展示/接单筛选 |
| `search_qualified_contractors` | 定向搜索接单方 | 按技能/认证/类型筛选 |

---

## 三、错误码兜底

错误码以 MCP 服务端实际返回为准；兜底动作指向 SKILL.md 第 4 步错误码兜底表（`references/opcs-errors.md`）：

| MCP 错误码（示例） | 触发条件 | 兜底动作 |
|---|---|---|
| `400 VALIDATION_ERROR` | 参数非法 | 提示回前置步骤；按实时 schema 校验失败回退骨架 |
| `403 FORBIDDEN` | 权限不足 | 提示角色切换或回 Web 端 |
| `404 NOT_FOUND` / `CONSULT_SESSION_EXPIRED` | 资源不存在/会话过期 | 提示刷新或重开 consult 会话 |
| `409 REVISION_MISMATCH` / `DRAFT_HASH_CONFLICT` | 修订号/hash 不匹配 | 重新拉最新草稿再 revise/重试 |
| `422 BUSINESS_RULE` | 业务规则违反 | 提示补 comment 后重试 |
| `429 RATE_LIMIT` | 调用超限 | 静默 1 分钟（L4 防线） |
| `500/503` | 服务端异常 | 提示重试或回 Web 端 |

---

## 四、与 SKILL.md 的关系

| 引用位置 | 内容 |
|---|---|
| **SKILL.md frontmatter allowed-tools** | 26 工具白名单（本文只列工具名，不列参数结构） |
| **SKILL.md 第 4 步** | 核心分支流程（consult 流 / draft_plan 展开 / 改需求 / 重试）+ 辅助场景说明 |
| **references/opcs-errors.md** | 错误码兜底映射（本文 §三 的详细版） |
| **references/consult-example.md** | consult 流转达示例 |
| **本文** | 工具白名单 + 用途速查 + 错误码兜底（不固化参数 schema） |
