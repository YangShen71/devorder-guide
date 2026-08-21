# DevOrder MCP 工具完整参考（v0.4.9.5 新增 8 工具签名文档）

> **配套文件**: SKILL.md frontmatter（allowed-tools 已扩展至 26 工具，v0.5.20 命名空间适配 DevOrder__*）
> **数据源**: `docs/business/opcs-mcp-research-report-20260813.md`（实测）+ 当前 MCP 服务（26 工具已启用）
> **匹配原则**: 严格对齐 MCP schema——方法名/参数名/参数类型/可选必填标记与 MCP 服务定义 100% 一致
> **v0.5.26 更新**: 移除旧版 `clientToken` 参数（首轮 M-4 遗留）——当前生产 MCP schema 以 `sessionId` 为会话标识；若工具实际返回 `clientToken` 字段再按需处理，不再预置说明。
> **v0.5.20 更新**: 命名空间从内部 opcs_* 后端方法名适配为 DevOrder MCP 工具名 DevOrder__*；当前 MCP 服务 26 工具全接入（v0.4.9.4~v0.4.9.5 共 22→26 演进完成）

---

## 一、已纳入 SKILL.md 的 26 工具分类

| 类别 | 工具 | 数量 |
|---|---|---|
| **顾问流（核心）** | consult, draft_plan, publish_plan | 3 |
| **顾问流（进阶，v0.4.9.4 新增）** | get_advisor_session, revise_order_draft, retry_publish, plan_document | 4 |
| **订单直建（兜底）** | create_order | 1 |
| **订单管理（基础）** | get_my_orders, get_order_detail, list_orders, list_bids, select_bid | 5 |
| **订单管理（进阶，v0.4.9.5 新增）** | get_my_order_detail | 1 |
| **里程碑管理** | add_milestone, configure_milestones, delete_milestone, update_milestone, list_milestones | 5 |
| **协议与账单** | draft_agreement, get_agreement, review_deliverable, get_bill | 4 |
| **资质认证（v0.4.9.5 新增）** | get_my_qualification, list_my_certification_tags | 2 |
| **接单方搜索（v0.4.9.5 新增）** | search_qualified_contractors | 1 |
| **合计** | — | **26** |

---

## 二、v0.4.9.5 新增 8 工具完整签名

### ① `DevOrder__get_advisor_session` — 获取顾问会话快照

> **中文注释**: 用于跨平台切换或长会话中断后的状态恢复——按 sessionId 拉取顾问会话快照（含 phase/facts 等**实际返回的字段**；`requirementVersion` 等字段仅当服务端返回时存在，不得假设必有），不需要再走一遍多轮提问。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sessionId` | string (1-128) | ✅ | consult 首轮返回的会话标识 |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `sessionId` | string | 透传 |
| `phase` | string | `gathering`（收集信息）/ `ready`（规划就绪）/ `proposal`（发布批次）；**以实际返回为准，未返回不得假设** |
| `reply` | string | 顾问最近一轮原话（用于断点后直接展示） |
| `facts` | object | `{已确认: {...}, 还需了解: [...]}` |
| `requirementVersion` | int | 需求版本号（**仅当服务端返回时存在**，不得假设必有） |
| `nextActions` | array | 建议下一步动作 |

**异常处理**:
- `404 CONSULT_SESSION_EXPIRED`: 会话过期/不存在 → 转 `DevOrder__consult`（不带 sessionId）开新会话
- `401 UNAUTHORIZED`: 未认证 → 引导登录

---

### ② `DevOrder__revise_order_draft` — 修改订单草稿

> **中文注释**: 用户在 draft_plan/publish_plan 之间反悔改需求（"预算改 5 万"、"目标人群换 30 岁以上"等）——不要重新走完整 consult 流，直接调本工具局部更新。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sessionId` | string (1-128) | ✅ | consult 返回的会话标识 |
| `planVersion` | int > 0 | ✅ | draft_plan/plan_document 返回的版本号 |
| `draftHash` | string (`^[a-f0-9]{64}$`) | ✅ | draft_plan/plan_document 返回的 64 位 hex |
| `expectedRevision` | int | ✅ | 当前订单草稿的修订号（防并发冲突） |
| `expectedOrderDraftHash` | string | ✅ | 当前订单草稿的 hash（防并发冲突） |
| `mode` | enum | ✅ | `UPDATE` / `RECONCILE_TASK_TYPES` / `REGENERATE_MODULE` |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `planVersion` | int | 修订后版本号 |
| `orderDraftHash` | string | 修订后订单草稿 hash |
| `orderDraftRevision` | int | 修订后订单草稿版本号 |

**三模式语义**:
- `UPDATE`: 局部更新（patch）
- `RECONCILE_TASK_TYPES`: 对齐 taskTypeCodes 与骨架模块
- `REGENERATE_MODULE`: 重生某个 module

**异常处理**:
- `409 REVISION_MISMATCH`: expectedRevision/expectedOrderDraftHash 不匹配 → 转 `DevOrder__draft_plan` 拉最新 hash 再 revise

---

### ③ `DevOrder__retry_publish` — 重试发布

> **中文注释**: `DevOrder__publish_plan` 失败时（5xx、网络中断、参数不一致）的幂等重试——schema 与 publish_plan 完全相同，含 `draftHash` + `orderDraftHash` **双重幂等键**避免重复发单。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sessionId` | string (1-128) | ✅ | consult 返回的会话标识 |
| `planVersion` | int > 0 | ✅ | draft_plan/plan_document 返回的版本号 |
| `draftHash` | string (`^[a-f0-9]{64}$`) | ✅ | draft_plan/plan_document 返回的 64 位 hex |
| `orderDraftRevision` | int | ✅ | 当前订单草稿修订号 |
| `orderDraftHash` | string | ✅ | 当前订单草稿 hash |
| `confirmed` | bool (const true) | ✅ | **必须由用户明示确认后传入**（红线⑨） |
| `confirmationText` | string (1-500) | ✅ | 用户明示确认的原文（如「发布」「确认」） |
| `company` | string | ❌ | 订单归属（与 create_order 一致） |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `orderId` | int | 订单 ID |
| `orderNo` | string | 订单号（DO 开头） |
| `publishedAt` | string (ISO) | 发布时间 |

**异常处理**:
- `409 DRAFT_HASH_CONFLICT`: 双重幂等键冲突 → 转 `DevOrder__get_my_orders` 查重
- `400 confirmed_missing`: 缺 confirmed/confirmationText → 必须由用户明示确认后传入

---

### ④ `DevOrder__plan_document` — 展开计划文档

> **中文注释**: 在 `DevOrder__draft_plan` 返回 `draftHash` 后跟调本工具，将简化计划展开为完整结构化文档（详化阶段任务、添加交付物规格、补充合同要点）。**顺序：先 draft_plan 后 plan_document，不反序。**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sessionId` | string (1-128) | ✅ | consult 返回的会话标识 |
| `planVersion` | int > 0 | ✅ | draft_plan 返回的版本号 |
| `draftHash` | string (`^[a-f0-9]{64}$`) | ✅ | draft_plan 返回的 64 位 hex |
| `model` | string | ❌ | 路由模型，默认 deepseek-v4-flash |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `planVersion` | int | 版本号 |
| `orderDraftHash` | string | 订单草稿 hash（用于 publish_plan） |
| `orderDraftRevision` | int | 订单草稿修订号（用于 publish_plan） |
| `planDocument` | object | 完整文档（含标题/阶段任务/交付物/合同要点） |

---

### ⑤ `DevOrder__get_my_order_detail` — 我的订单详情（含当事方私有字段）

> **中文注释**: 当前用户作为当事方（issuer/picker）的订单详情，**较 `DevOrder__get_order_detail` 增加 `onlyVisibleToRoles` 私有段**（含真实联系方式、付款方内部信息等）。当订单存在但当前用户非当事方时返回 404。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `orderId` | int / 数字 string | ✅ | 订单 ID |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| （与 get_order_detail 相同 + `onlyVisibleToRoles` 私有段）| object | 当事方可见的完整字段 |

**与 `DevOrder__get_order_detail` 的区别**:
- `get_order_detail`: 任何角色可查的脱敏版（公开订单详情）
- `get_my_order_detail`: 当前用户作为当事方的详情（私有字段）

**异常处理**:
- `404 NOT_FOUND`: 订单不存在或当前用户非当事方

---

### ⑥ `DevOrder__get_my_qualification` — 我的主体资格

> **中文注释**: 读取当前主体身份/资质审批状态/能力/权限标志——通常在写工具调用前查询 `permissions.canCreateOrder` / `canBidOrder` 决定前置条件。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 无 | — | | |（公开工具，不需要令牌） |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `identity.role` | enum | `CUSTOMER` / `CONTRACTOR` |
| `identity.profileExists` | bool | 资料是否完整 |
| `qualification.status` | enum | `APPROVED` / `PENDING` / ... |
| `qualification.approved` | bool | 是否已审核通过 |
| `qualification.statusLabel` | string | 状态中文标签 |
| `capabilities` | object | `{companyName, ...}` |
| `permissions.canCreateOrder` | bool | 是否有发单权限 |
| `permissions.canBidOrder` | bool | 是否有接单权限 |
| `nextActions` | array | 建议下一步动作（如完善资料）|

**示例调用场景**:
- 第 3 步准备调 `DevOrder__create_order` 或 `DevOrder__publish_plan` 前，先调本工具确认 `canCreateOrder=true`
- 用户表达"接单"意图时，先确认 `canBidOrder=true` 再走接单路径

**异常处理**:
- `401 UNAUTHORIZED`: 未登录 → 引导登录

---

### ⑦ `DevOrder__list_my_certification_tags` — 我的认证标签

> **中文注释**: 获取当前主体已持有 / 可申请 / 申请中的认证标签集合（如 `官方推荐服务商` / `金牌合作伙伴` / 行业专家等）——用于发单时展示发单方资质或接单时筛选认证服务商。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 无 | — | | |（issuer / picker 通用） |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `heldTags` | array | 已持有标签 `[{tagCode, tagName}]` |
| `availableTags` | array | 可申请标签 |
| `applications` | array | 申请中的标签 |
| `nextActions` | array | 建议下一步（如申请标签） |

**示例调用场景**:
- 发单方筛选接单方时用 `certificationTagCodes` 过滤（如"只要金牌合作伙伴"）
- 在对话中告知用户"你当前是『金牌合作伙伴』资质，可申请更多标签"

---

### ⑧ `DevOrder__search_qualified_contractors` — 搜索合格接单方

> **中文注释**: 按技能/行业/认证标签筛选可指派的接单方——发单方在创建定向订单时可指定"必须金牌合作伙伴 + 具备 React 技能 + 行业专家认证"的接单方范围。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string (1-100) | ❌ | 关键字搜索 |
| `skills` | array[string] (1-20) | ❌ | 技能标签，如 `["react", "vue"]` |
| `industryTags` | array[string] (1-20) | ❌ | 行业标签 |
| `certificationTagCodes` | array[string] (1-20) | ❌ | 认证标签码，如 `官方推荐服务商` / `金牌合作伙伴` |
| `contractorType` | enum | ❌ | `individual` / `team` / `company` |
| `page` | int (默认 1) | ❌ | 页码 |
| `pageSize` | int (1-50, 默认 10) | ❌ | 分页大小 |

| 返回字段 | 类型 | 说明 |
|---|---|---|
| `items` | array | 接单方列表 `[{contractorRef, displayName, contractorType, capabilityIntro, skills[], industryTags[], certifiedTags[], completedOrderCount}]` |
| `total` | int | 满足条件的接单方总数 |

**异常处理**:
- `401 UNAUTHORIZED`: 未登录 → 引导登录

---

## 三、参数校验与默认值总表

| 工具 | 必填字段校验 | 默认值处理 |
|---|---|---|
| `get_advisor_session` | sessionId 必传且非空字符串 | —（以 sessionId 为准） |
| `revise_order_draft` | sessionId + planVersion > 0 + draftHash 64hex + expectedRevision + expectedOrderDraftHash + mode (枚举) | — |
| `retry_publish` | 同 publish_plan：sessionId + planVersion + draftHash + orderDraftRevision + orderDraftHash + confirmed=true + confirmationText 1-500字 | company 默认从令牌身份 |
| `plan_document` | sessionId + planVersion > 0 + draftHash 64hex | model 默认 deepseek-v4-flash |
| `get_my_order_detail` | orderId 必传且为合法整数/数字字符串 | —（以 sessionId 为准） |
| `get_my_qualification` | 无参数 | 公开工具 |
| `list_my_certification_tags` | 无参数 | issuer/picker 通用 |
| `search_qualified_contractors` | 无必填 | page 默认 1；pageSize 默认 10，最大 50；其他筛选器默认不启用 |

---

## 四、输出解析与异常处理一致性

8 个工具的返回结构均与 MCP schema 严格匹配；异常处理路径均指向 SKILL.md §3 第 3 步错误码兜底表。错误码与 MCP 真实错误码一致：

| MCP 错误码 | 触发条件 | 引导层动作 |
|---|---|---|
| `400 VALIDATION_ERROR` | 参数非法 | 引导回前置步骤；按 schema 校验失败回退骨架（红线⑧） |
| `403 FORBIDDEN` | 权限不足 | 引导角色切换或回 Web 端 |
| `404 NOT_FOUND` / `CONSULT_SESSION_EXPIRED` | 资源不存在/会话过期 | 引导刷新或重新开 consult 会话 |
| `409 REVISION_MISMATCH` / `DRAFT_HASH_CONFLICT` | 修订号/hash 不匹配 | 重新拉最新草稿再 revise/重试 |
| `422 BUSINESS_RULE` | 业务规则违反 | 引导补 comment 后重试 |
| `429 RATE_LIMIT` | MCP 调用超限 | 引导层静默 1 分钟（L4 防线） |
| `500/503` | 服务端异常/不可用 | 引导重试或回 Web 端 |

---

## 五、调用示例（伪代码）

```python
# === 跨平台恢复 ===
session_state = DevOrder__get_advisor_session(sessionId="do_xxx")
phase = session_state["phase"]
facts = session_state["facts"]
# 带着 facts 继续调 consult，保持多轮

# === 用户改需求 ===
revise_resp = DevOrder__revise_order_draft(
    sessionId="do_xxx",
    planVersion=3,
    draftHash="a3f0...e21c",
    expectedRevision=2,
    expectedOrderDraftHash="b9d2...af7e",
    mode="UPDATE",
    patch={"audience": "30 岁以上"}
)

# === publish_plan 5xx 重试 ===
publish_resp = DevOrder__retry_publish(
    sessionId="do_xxx", planVersion=3,
    draftHash="a3f0...e21c", orderDraftRevision=5,
    orderDraftHash="b9d2...af7e",
    confirmed=True,
    confirmationText="用户在我的手机上点击了'确认发布'按钮"
)

# === 资质前置检查 ===
qual = DevOrder__get_my_qualification()
if qual["permissions"]["canCreateOrder"]:
    # 进入第 3 步 consult 流
    ...

# === 接单方筛选 ===
contractors = DevOrder__search_qualified_contractors(
    certificationTagCodes=["金牌合作伙伴"],
    skills=["react"],
    contractorType="team",
    pageSize=10
)
```

---

## 六、与 SKILL.md 的关系

| 引用位置 | 内容 |
|---|---|
| **SKILL.md frontmatter allowed-tools** | 30 工具白名单（含本文档 8 工具） |
| **SKILL.md 第 3 步** | 4 个核心分支（跨平台/draft_plan 展开/改需求/重试）+ 4 个辅助场景说明（资质前置/认证/接单方/详情） |
| **references/opcs-errors.md** | 错误码兜底映射 |
| **references/consult-example.md** | 异常分支表引用本文档工具 |
| **本文档** | 8 工具完整签名/参数/返回/异常处理（本文） |