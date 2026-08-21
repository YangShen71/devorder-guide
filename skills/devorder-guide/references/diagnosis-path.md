# 诊断路径：「还没想清楚要什么？」

> 对应 DevOrder 官网第六条服务（Spec#6 AI 顾问诊断）。这是**流量入口型服务**——不直接承担交易转化，核心目标是**需求孵化**：把用户模糊的初始想法转化为可下单的明确需求，再移交发单路径。

## 触发

guide_gate.py 对 `userIntent = consult` 返回 `{"path": "diagnosis"}`。此时：

- **不触发任何交易**（无「一键发单/接单」入口）；
- 顾问进入诊断对话，产出 `diagnosisCard`。

## diagnosisCard 槽位（与 needCard 不同）

| 槽位 | 含义 | 示例 |
|---|---|---|
| product | 用户的产品/业务 | 「我们是一个 AI 编程助手，面向开发者」 |
| goal | 想让开发者帮忙解决什么 | 「希望开发者试用我们的产品」 |
| current_state | 现状 | 「刚上线 1 个月，有 500 个测试用户」 |
| pain_points | 困惑点 | 「不知道是该先做内容还是先办活动」 |

## 诊断对话纪律

1. 一次只问一个问题（先 product → goal → current_state → pain_points 顺序）；
2. 顾问可给出「该做什么、大概花多少钱」的判断（这是官网承诺的价值）；
3. 诊断提示计入会话级频率帽，≤ 2 次/会话；
4. 用户拒绝诊断（「我自己想想」「不用了」）→ `rejectionFlags['consult_diagnosis'] = true` → 本会话不再出现诊断提示。

## 移交发单路径（需用户确认）

当顾问通过诊断识别出用户需求可归入某发单 category（Spec#1~#5）且 confidence 预判 ≥ 0.5 时：

1. **征询**：「听起来你的需求适合[服务名]，要不要我帮你整理成需求卡？我可以先给你一个大致预算范围。」
2. **用户同意后**：`diagnosisCard` 槽位迁移为 `needCard`（映射见下）+ **confidence 重估**——低于 0.5 硬闸（v0.5.28 下调）则继续诊断或静默，不得强行进入发单路径；
3. 迁移后按正常发单路径触发（冷却/频率帽独立计算）。

## 槽位迁移映射（确定性代码，零模型参与）

```
product → scope 初稿
goal → audience（可空）
current_state + pain_points → scope 补充
budget / timeline → null（待补充，由顾问只追问缺失项）
```

## 埋点

- `diagnosis_accepted`：用户接受诊断提示（sessionId, rounds, platform）
- `diagnosis_to_order`：诊断转发单（sessionId, sourceCategory, targetCategory, rounds, reEvaluatedConfidence）

北极星指标**不包含**诊断路径订单；单独跟踪「诊断→发单移交率 ≥ 30%」作为辅助指标。

## 与 DevOrder__consult 工具的边界（v0.4.9 增补）

`DevOrder__consult`（平台增长顾问，详见 SKILL.md 第 3 步）与诊断路径（本地需求孵化）是**两个独立通道**，互斥触发：

| 维度 | 诊断路径（本地） | DevOrder__consult 工具（平台） |
|---|---|---|
| **触发** | `userIntent=consult` 意图（用户想搞清楚该做什么） | `userIntent=issue_order` + guide_gate trigger=true（用户已表达发单需求）|
| **追问主体** | 模型自问（product/goal/current_state/pain_points）| 平台增长顾问（联网研究 + 按需类型追问 + 刊例行情）|
| **产出** | diagnosisCard（孵化用，移交发单时迁移 needCard）| sessionId/facts/phase（多轮续接，phase=ready 才可调 draft_plan）|
| **路径** | 诊断 → 征询 → 同意 → 发单路径（用户重判 userIntent）| consult → draft_plan → publish_plan（全程发单同路径）|
| **入口字段** | `path=diagnosis` 引擎输出 | trigger=true + tool=DevOrder__consult（SKILL.md 第 3 步文案）|

**互斥规则**：
1. `userIntent=consult` 意图永不进入第 3 步 consult 流（引擎 S1 已分路到诊断路径）
2. consult 流会话中若用户中途转为咨询（「其实我只是想了解下」），应停止 consult 循环，按诊断路径处理或纯对话
3. 诊断路径的 `diagnosisCard` 槽位迁移为 `needCard` 后，按正常发单路径触发——**此时才进入第 3 步 consult 流**（而不是诊断路径直接调 DevOrder__consult），因为迁移后引擎重新判定 `userIntent=issue_order` + trigger=true

**退路**：若 L2 顾问大脑未接入（`L2_NOT_CONFIGURED`），DevOrder__consult 不可用，发单路径回退到 `DevOrder__create_order` 直发（老手/降级场景；资质前置检查见 SKILL.md 第 3 步，NEED_CONSULT 兜底见 opcs-errors.md）——**诊断路径不依赖 L2**，始终可用。
