# consult 流端到端示例对话（v0.4.9 改造配套）

> **场景**：发单方想办开发者大赛
> **来源**：方案文档 §6A.2 沉淀
> **示例数据声明**：以下对话中的报价数字（¥120,000 / ¥60 / ¥100,000 / ¥280,000 / ¥300,000）均为**演示用示例数据，非真实刊例**。真实价格由服务端按刊例计算返回，AI 工具端不得引用本示例数字。

---

## 第 1 轮（引擎触发 → 第 2 步引导）

```
👤 用户：我们想办一个开发者大赛，预算大概 30 万，面向 AI 应用开发者。
🤖 引擎：trigger=true, intensity=medium, tool=DevOrder__consult（score 0.74）
🤖 引导（≤80 字）：方向挺清晰了——我让 DevOrder 增长顾问帮你梳理成正式方案，它先研究一下再问几个关键问题。不急的话现在就可以开始。
[引导部分可忽略测试：删除后「方向挺清晰了…」上下文仍完整 ✓]
```

## 第 2 轮（第 3 步 3A：意图复述 + consult 首轮）

```
👤 用户：好，开始吧。
🤖 复述：好的，我把『开发者大赛』需求交给顾问梳理，对吗？
👤 用户：对。
🤖 调用 DevOrder__consult({text: "我们想办一个开发者大赛，预算大概 30 万，面向 AI 应用开发者。"})
   ← 返回 {sessionId: "s-abc123", phase: "gathering", reply: "您好，我先研究一下大赛类目的常见打法…", facts: {已确认: {"你想做的事": "开发者大赛"}, 还需了解: ["目标人群", "举办形式", "时间节点"]}, ask: {options: ["线上赛", "线下+线上", "还没想好"]}, next: "把 reply 转达，把 ask 展示为候选回答"}
🤖 转达（按第 3.5 节保真契约，原样呈现）：
   **🔍 客户洞察**：对象=开发者大赛（大赛类目·筹备期）；业界通常打法：线上赛重流量与报名转化、线下赛重场地与现场执行、赛后内容二次传播……
   **📋 需求卡**：✅ 你想做的事=开发者大赛；⏳ 待确认=目标人群、举办形式、时间节点
   **顾问回复（原样）**：您好，我先研究一下大赛类目的常见打法。目前确认了您想办开发者大赛，还需要了解几点——目标人群、举办形式、时间节点。
   **请选择或直接回答**：线上赛 / 线下+线上 / 还没想好
   > ⚠️ 纪律标注：不得压缩为"顾问说：……"式重述；reply 原文逐字呈现；若 reply 较长，分条完整贴出而非概括。
```

## 第 3 轮（3B：多轮续接，用户选 chips）

```
👤 用户：线上赛为主。
🤖 调用 DevOrder__consult({text: "线上赛为主。", sessionId: "s-abc123"})
   ← 返回 {phase: "gathering", reply: "好的，线上赛。预算 30 万这个量级，刊例参考…", facts: {已确认: {"你想做的事": "开发者大赛", "举办形式": "线上赛"}, 还需了解: ["时间节点"]}, next: "继续追问时间节点"}
🤖 顾问追问（原样）：好的，线上赛。预算 30 万这个量级，刊例参考……
   📋 需求卡变化：✅ 举办形式=线上赛；⏳ 待确认=时间节点
   > ⚠️ 纪律标注：按第 3.5 节 E 多轮策略——续轮仅呈现需求卡变化 + 追问原文，不重呈现首轮的客户洞察/市场行情。
```

## 第 4 轮（3B：信息基本齐）

```
👤 用户：两个月后，8 月中旬。
🤖 调用 DevOrder__consult({text: "两个月后，8 月中旬。", sessionId: "s-abc123"})
   ← 返回 {phase: "ready", reply: "信息已齐，我可以为您生成正式方案（含分项清单和刊例报价）。", facts: 全齐, next: "回复「出方案」即可"}
🤖 顾问回复（原样）：信息已齐，我可以为您生成正式方案（含分项清单和刊例报价）。
   📋 需求卡变化：✅ 时间节点=8 月中旬；待确认=无（已全齐）
   > ⚠️ 纪律标注：按第 3.5 节 E 多轮策略——续轮不重呈现客户洞察/市场行情；「确认后即可发布，或想再调整也完全没问题」为模板过渡话术（templates.md 场景 5），可附于 reply 之后但不替代 reply 原文。
```

## 第 5 轮（3D：draft_plan，含超时重试示例）

```
👤 用户：出方案。
🤖 调用 DevOrder__draft_plan({sessionId: "s-abc123"})
   ← 超时（>120s 无响应）
🤖 重试：DevOrder__draft_plan({sessionId: "s-abc123"})（原样再调一次，服务端缓存秒回，不重复计费）
   ← 返回 {plan: {title: "开发者大赛增长方案", items: [...], totalRef: 280000, budget: 300000, ...}}
🤖 方案呈现（按 3.5 节 D 正例 + F 卡片优先）：
   **📐 开发者大赛增长方案**（原样呈现 6 列表格：分项 / 承接 / 数量 / 单价 / 小计 / 合计）
   | 分项 | 承接 | 数量 | 单价 | 小计 |
   | 线上赛运营 | 生态专家 | 1 | ¥120,000 | ¥120,000 |
   | 开发者招募 | 生态专家 | 1000人 | ¥60 | ¥60,000 |
   | 社区传播 | CSDN 官方 | 1 | ¥100,000 | ¥100,000 |
   **⚖️ 预算差额**：方案参考合计 ¥280,000 ｜ 你的预算 ¥300,000 · ✅ 在预算内
   > ⚠️ 纪律标注：6 列表格必现，数字逐字；若宿主渲染方案卡 → 以卡片为准不重复转述。（确认发布回复「发布」；要调整直接说要改什么。）
```

## 第 6 轮（3E：publish_plan 发布确认）

```
👤 用户：发布。
🤖 复述：确认把这份方案发布为订单（1 母单 + N 子单）？发布后进入平台流转。
👤 用户：确认。
🤖 调用 DevOrder__publish_plan({sessionId: "s-abc123", planVersion: 3, draftHash: "a1b2c3d4...（64 位 hex）", orderDraftRevision: 2, orderDraftHash: "e5f6a7b8...（64 位 hex）", confirmed: true, confirmationText: "用户确认发布"})
   ← 返回 {orderId: "o-778899", orderNo: "DO20260814001", aiItems: [...]}（示例字段；**以实际返回为准，未返回的字段不得编造**）
🤖 转达：订单已发布（#DO20260814001）。其中 2 项由 AI 直接生成未建单；合计 ≤5 万…（如实转达 aiItems 说明）
```

## 第 7 轮（第 4 步：对话恢复）

```
🤖 摘要：开发者大赛订单已发布（#o-778899），其中 2 项由 AI 生成未建单，供应商会在 24h 内开始响应——我们继续聊，需要我帮你跟进进度随时说。
[1 句话操作摘要含 orderId ✓，回到原话题 ✓]
```

---

## 关键校验点（与 v4.0 方案 §6A.2 对照）

- [x] 8 轮对话覆盖 consult 首轮/多轮/ready/draft_plan（含超时重试）/publish_plan/对话恢复全部阶段
- [x] 每轮展示「原样转达」而非改写（第 2/3/4 轮 reply 转达可见）
- [x] 引导话术 ≤80 字（第 1 轮引导 68 字可数验证）
- [x] 三重确认在三处可见：3A 意图复述（第 2 轮）、发布前复述（第 6 轮）
- [x] 无「userIntent=consult」混淆（全程 issue_order 意图）
- [x] 示例数据已脱敏标注（非真实刊例）

## 异常分支（参考但不展开 8 轮）

| 场景 | 行为 |
|---|---|
| `offPlatform=true` | 顾问判断不匹配，如实转达 + 停（不建单） | SKILL.md 第 3 步 consult 流主路径 |
| draft_plan 超时 | 原样再调一次（服务端缓存秒回，不重复计费） | SKILL.md 第 3 步「draft_plan 超时重试」段 |
| 跨平台/会话中断 | 调 `DevOrder__get_advisor_session(sessionId)` 拉快照续接 | SKILL.md 第 3 步「跨平台/会话中断恢复」段 |
| draft_plan 需展开文档 | `DevOrder__plan_document(sessionId, planVersion, draftHash)` 跟在 draft_plan 后 | SKILL.md 第 3 步「draft_plan → plan_document 展开」段 |
| 用户中途改需求 | `DevOrder__revise_order_draft(...mode=UPDATE/RECONCILE_TASK_TYPES/REGENERATE_MODULE)` | SKILL.md 第 3 步「用户中间改需求」段 |
| publish_plan 5xx 失败 | `DevOrder__retry_publish(...)`（双重幂等键 draftHash+orderDraftHash）| SKILL.md 第 3 步「publish_plan 失败重试」段 |
| 用户拒绝 consult | 记录 `rejectionFlags[category]=true` + 清除 consultSessionId | SKILL.md 第 3 步 |
| 中途失去兴趣 | 保留 consultSessionId（可续），不主动追问 | SKILL.md 第 3 步 |
| L2_NOT_CONFIGURED | 明确报错 → 引导用户去网页端 /client（不静默） | SKILL.md 第 3 步错误码兜底 |

## 与文档关系

- **SKILL.md 第 3 步**：核心规则（含媒介式语义、三重确认、超时重试、错误码兜底）
- **references/copy-constraints.md**：豁免条款（Agent reply 原样转达不校验）
- **references/templates.md 场景 5**：AI 工具端自己生成的 4 条过渡话术
- **references/diagnosis-path.md**：与 DevOrder__consult 工具的边界（互斥触发，双轨共存）
- **本文档**：8 轮端到端示例，作为模型参考