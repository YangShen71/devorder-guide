# DevOrder MCP 错误码兜底映射（opcs 后端 API 错误码）

> **依据**：reports/audit/opcs-schema-audit-20260804.md + DevOrder MCP 服务端错误语义（opcs 后端 Java API 定义）
> **兜底原则**：4xx 业务错误 → 对话内继续处理（401/403/503 除外）；5xx 系统错误 → 提示回 Web 端；429 限流 → 兜底层静默 1 分钟（不重复触发 opcs 调用）

| 错误码 | 含义 | 兜底话术方向 | 兜底动作 |
|---|---|---|---|
| 400 VALIDATION_ERROR | 字段非法 | 「你刚才说的 [字段] 可能不太准确，能再补充下吗？」 | 提示回前置步骤；按 schema 校验失败回退骨架（红线⑧） |
| 401 UNAUTHORIZED | 未登录/令牌过期 | 「需要先登录 DevOrder 账号，方便我帮你完成 [操作]」 | 提示登录（OAuth 回 Web 端） |
| 403 FORBIDDEN | 权限不足（非订单当事方/角色不符） | 「这个操作需要 [角色] 权限，或该订单仅限当事方操作」 | 提示角色切换或回 Web 端 |
| 404 NOT_FOUND | 资源不存在（订单/里程碑/协议） | 「没找到这个 [订单/里程碑/协议]，要不换个试试？」 | 提示刷新或回列表 |
| 409 STATE_INVALID | 状态非法（订单未履约/未选接单方/已取消） | 「这个订单当前处于 [状态]，暂不能 [操作]」 | 提示回列表或查看详情 |
| 422 BUSINESS_RULE | 业务规则违反（如验收驳回未填原因） | 「驳回需要说明原因，方便服务商改进」 | 提示补 comment 后重试 |
| 429 RATE_LIMIT | MCP 调用超限 | 「操作太频繁了，稍等一下再试」 | 兜底层静默 1 分钟（L4 防线） |
| 500 SERVER_ERROR | 服务端异常 | 「平台这边暂时有点问题，咱们等会儿再试」 | 提示重试或回 Web 端 |
| 503 SERVICE_UNAVAILABLE | 服务不可用 | 「服务暂时不可用，建议去 DevOrder 网页端继续操作」 | **回 Web 端兜底** |
| L2_NOT_CONFIGURED | 顾问大脑未接入本机 | 「顾问服务暂不可用，建议去 DevOrder 网页端 /client 继续梳理」 | 回 Web 端兜底 |
| L2_TIMEOUT / L2_UNREACHABLE | 顾问调用超时/连不上 | 「顾问这边响应有点慢，我帮你再试一次」 | 原样重试一次（draft_plan 幂等）|
| CLIENT_TOKEN_REQUIRED | 缺发单方令牌 | 「需要先配置 DevOrder 发单方令牌，或登录网页端操作」 | 提示配置/回 Web |
| NEED_CONSULT | create_order 缺料被拦 | 「发单前还需确认：［missing 清单］」 | 服务端已自动转接顾问，照常转达 |
| CONSULT_SESSION_EXPIRED | get_advisor_session 会话过期/不存在 | 「这段梳理会话已过期，我重新帮你起一段——你刚才说的关键信息能再简单复述一下吗？」 | 重新调 consult（不含 sessionId）开新会话 |
| REVISION_MISMATCH | revise_order_draft expectedRevision/expectedOrderDraftHash 不匹配 | 「你刚才修改时草稿已更新，再调整可能冲突——要不我再拉一下最新草稿，你说改哪里？」 | 重新调 draft_plan 拉最新 hash 再 revise |
| DRAFT_HASH_CONFLICT | retry_publish / publish_plan 幂等键冲突 | 「订单已用相同草稿发起了，避免重复发单——你看一下订单状态是否正常」 | 调 get_my_orders 查重，已有就不重试 |
| INVALID_ARGUMENT | 工具参数不符合契约 | 「[参数] 有点问题，我核对下最新格式再试」 | 按实时 schema 重传；**禁止臆造参数重试** |
| RESPONSE_SCHEMA_MISMATCH | 响应校验失败（**写操作可能已成功**） | 「刚才的操作可能已提交成功，我先帮你核对一下结果」 | **先调对应只读工具核对**（get_my_orders / get_order_detail / list_milestones），**确认未落库才可重试**；禁止盲重试 |
| INTERNAL_ERROR | 服务端内部异常 | 「平台这边出了点问题，已记录编号 [requestId]，可凭此排查」 | 记录返回的 requestId 供排查；**不自动重试** |

## 通用规则：响应不符契约 ≠ 调用失败（防重复写）

所有写工具（create_order / publish_plan / revise_order_draft / configure_milestones / review_deliverable 等）遇到**任何异常响应**（含 RESPONSE_SCHEMA_MISMATCH），一律**先只读核对再决定重试**——写操作可能已在服务端落库，盲重试会导致重复建单/重复扣款。核对路径：get_my_orders（订单）→ get_order_detail（详情）→ list_milestones（里程碑），按资源类型就近选择。

## 硬门禁相关（userConfirmation / confirmed）

| 场景 | 兜底动作 |
|---|---|
| 写工具（create_order/select_bid/milestone/review）返回 userConfirmation 缺失错误 | 说明：必须完成三重确认第 3 层（用户明确同意「本次提交」）后才传 userConfirmation=true（红线⑨） |
| publish_plan / retry_publish 返回 confirmed 缺失错误 | 说明：必须由用户明示确认（如「发布」「确认」）后传 confirmed=true 与 confirmationText（1-500 字，记录用户确认原文）|
| 代理尝试擅自传 true | 禁止——opcs 硬门禁会拒绝；兜底层必须在用户明确同意后操作 |

## 兜底话术合规约束

- 所有兜底话术 ≤ 80 汉字、含退路、无绝对化词（过 check_copy）
- 「回 Web 端」话术同一会话同类 ≤ 1 次（计入会话级帽）
