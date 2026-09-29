# 上下文状态管理（state-management）

> **何时读取本文件**：当需要维护会话状态字段时——获取 10 字段契约表（谁读写、何时写）+ ctx 组装模板。

---

## 上下文状态管理

会话级状态由**模型维护**（闸门是无状态过滤器，只读 ctx 不写）。字段契约见 [configs/contract.json](configs/contract.json)。

### 状态维护者明细（谁读写、何时写）

| 字段 | 谁写 | 何时写 | 说明 |
|---|---|---|---|
| `needCard` | 模型 | 用户表达需求时建立/更新 | 槽位填充驱动 slotFill；诊断移交发单时按 diagnosis-path 映射 |
| `diagnosisCard` | 模型 | 用户走诊断路径时 | 移交发单时重估 confidence（低于 0.5 硬闸不得进入发单）|
| `guideHistory` | 模型 | 每次触发后追加 | `{category, ts, intensity, outcome, subtype}`——冷却与频率帽数据源 |
| `rejectionFlags` | 模型 | 用户忽略/拒绝后 | **键 = category**（含 `consult_diagnosis`）与 **`order_pick`**（接单路径拒绝，防接单 weak 空转）|
| `postRejectionWeakShown` | 模型 | 拒绝后放行weak时 | `{category → bool}`——已给过的类别不再给（≤1 次/会话）|
| `consecutiveRejections` | 模型 | 用户拒绝时递增 | ≥2 → 熔断，本会话不再触发任何（累计 ≥2 次即熔断，防打扰优先；「连续忽略降级」「高频熔断 1h」已放弃）|
| `opcsCallsLastMinute` | 模型 | 调用 opcs 前粗粒度统计 | 尽力而为（模型无法精确统计真实调用数，缺省 0 = 不触发 L4）|
| `activeOrders` | 模型 | 每轮从平台状态同步 | 非空 → R6 静默（进行中交易不干扰）|
| `guideCountThisHour` | 模型 | 每轮自增 | ≥3 → 本会话静默 30 分钟（会话级频率帽；跨会话不累计——防打扰兜底由服务端 L4 限流 `opcsCallsLastMinute` 承担）|
| `diagnosisCount` | 模型 | 每次诊断提示后递增 | ≥2 → 诊断静默（引擎强制，详见 diagnosis-path.md）|
| `consultSessionId` | 模型 | consult 首轮返回后 | 平台侧会话键；续接必须带回；完成/放弃后清除（模型级字段，不进 contract.json 引擎契约）|
| `consultPhase` | 模型（读） | 每轮 consult 返回后 | 顾问 phase：gathering/ready/proposal；ready 才可调 draft_plan（与引擎 R4 phase 区分，不进引擎 ctx）|
| `consultFacts` | 模型（读） | 每轮 consult 返回后 | 已确认/还需了解；用于向用户同步进度（不改变引擎判定）|
| `relayFidelityChecked` | 模型 | 每次 consult/draft_plan 转达后 | **新增**——true=已对照 5 区块自检或跑过 fidelity_check |
| `relayFidelityRate` | 模型 | fidelity_check 跑过后 | **新增**——0.0~1.0 保真率 |

### ctx 组装模板（发单路径示例）

```json
{
  "sessionId": "s1", "platform": "workbuddy", "platformCompatible": true,
  "userIntent": "issue_order", "category": "event", "subtype": "competition",
  "confidence": 0.8, "phase": "gather", "slotFill": 0.6, "round": 5,
  "guideCountThisHour": 0, "lastSameCategoryMinutesAgo": 20,
  "rejectionFlags": {}, "postRejectionWeakShown": {}, "consecutiveRejections": 0,
  "activeOrders": [], "userRole": "issuer", "guideHistory": [],
  "painKeywords": true, "goalKeywords": false, "specType": "dedicated",
  "matchedOrderCount": 0, "orderQuality": null, "hasNewDemandSignal": false
}
```

> **拿不准一律 consult**：意图预分类置信度不足时显式降级为 `userIntent: "consult"`（走诊断路径，不触发交易）。**3 个危险字段（activeOrders / guideCountThisHour / lastSameCategoryMinutesAgo）缺失 → 引擎 fail-closed 静默**（宁可静默不触发）；其余字段取契约默认值（多数 fail-safe）——建议宁可显式填默认值也不要省略字段。
>
> **最小差异组装**：不必每轮输出完整 28 字段——只需写**变化的字段 + 3 个危险字段**（activeOrders/guideCountThisHour/lastSameCategoryMinutesAgo 必须显式），其余按 contract.json 默认值（sessionId 可复用、confidence/slotFill/round 每轮更新、意图类字段变化时更新）。典型每轮 6~9 个字段即可。

