#!/usr/bin/env python3
"""DevOrder 引导闸门 — 确定性触发引擎（《AI 工具对话引导方案 v1.4》§3 实现）

实现 S0~S6 决策路径：频率帽 → 平台兼容 → 意图分路 → 硬规则闸(R1~R7) → 拒绝分支 → 打分 → 强度选择 → 工具选择。
零模型自由度：本脚本的输出是"是否引导、什么强度、什么入口"的唯一来源。

用法：
    python guide_gate.py --context '<json>'
    或通过 stdin 传入 JSON。
输出：JSON，含 trigger / intensity / tool / score / reason / path。

设计基线（修改需走方案评审，v1.4 §0.3）：
- 阈值 0.5；置信度硬闸 0.75；全局频率帽 3 次/小时；同类冷却 10 分钟
- 强度规则（v0.5.22 阈值下调后）：拒绝→weak（需新信号）；category 命中 5 品类且 score≥0.5 → strong；
            score≥0.6 且 slotFill≥0.65 → strong；score≥0.5 → medium
"""

import argparse
import json
import sys

# ---------------- 常量 ----------------
VALID_CATEGORIES = {"dev_growth", "user_acquisition", "event", "community", "exposure"}
DIAGNOSIS_CATEGORY = "consult_diagnosis"
INTENTS = {"issue_order", "pick_order", "consult", "chitchat", "service_query"}
DIAGNOSIS_MAX_PER_SESSION = 2  # 诊断提示 ≤2 次/会话（diagnosis-path.md，2026-08-05 P0-1 引擎强制）


# 2026-08-05 验收报告 P0-2：常量单一数据源——引擎启动时加载 configs/constants.json，
# 数值常量与 opcs_role_tool_map 以配置文件为唯一口径（消除双写；check_config 漂移检查保留）
def _load_constants() -> dict:
    """加载 constants.json；缺失时回退模块默认值（fail-safe）。"""
    try:
        import json as _json
        from pathlib import Path

        cfg_path = Path(__file__).resolve().parent.parent / "configs" / "constants.json"
        if cfg_path.exists():
            return _json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


_CFG = _load_constants()

DEFAULT_THRESHOLD = _CFG.get("DEFAULT_THRESHOLD", 0.5)
STRONG_SCORE = _CFG.get("STRONG_SCORE", 0.6)
CONFIDENCE_GATE = _CFG.get("CONFIDENCE_GATE", 0.75)
GLOBAL_CAP_PER_HOUR = _CFG.get("GLOBAL_CAP_PER_HOUR", 3)
CATEGORY_COOLDOWN_MINUTES = _CFG.get("CATEGORY_COOLDOWN_MINUTES", 10)
STRONG_SLOT_FILL = _CFG.get("STRONG_SLOT_FILL", 0.65)
HISTORY_FIXED = _CFG.get("HISTORY_FIXED", 0.3)  # 单令牌架构固定档位；OAuth 后解锁动态取值
L4_RATE_LIMIT_PER_MIN = _CFG.get("L4_RATE_LIMIT_PER_MIN", 100)  # L4 令牌级限流（业务报告 §5.4.5）
L4_SILENT_SECONDS = _CFG.get(
    "L4_SILENT_SECONDS", 60
)  # L4 超限后静默时长（与 opcs-errors.md 429 一致）

GUIDE_WEIGHTS = {
    "spec_clarity": 0.30,
    "pain": 0.25,
    "slot_fill": 0.20,
    "history": 0.15,
    "round": 0.10,
}
PICK_WEIGHTS = {"skill_match": 0.40, "order_quality": 0.30, "history": 0.15, "round": 0.15}


def _c(ctx, key, default):
    """读取上下文字段，缺省取默认值（容忍缺字段，旧会话走默认）。"""
    return ctx.get(key, default)


# ---------------- S0：全局频率帽 ----------------
def check_frequency_cap(ctx):
    count = _c(ctx, "guideCountThisHour", 0)
    if count >= GLOBAL_CAP_PER_HOUR:
        return (
            False,
            f"全局频率帽：本小时已展示 {count} 次引导（≥{GLOBAL_CAP_PER_HOUR}），全局静默 30 分钟",
        )
    return True, None


# ---------------- S0.1：L4 令牌级速率限制（业务报告 §5.4.5「频率限制：100 次/分钟/令牌」） ----------------
def check_l4_rate_limit(ctx):
    """L4 令牌级限流：opcs MCP 调用速率 ≥ 100 次/分钟 → 静默，不触发新的 opcs 调用。

    业务依据：DevOrder 业务需求报告 §5.4.5 开放层约束「MCP 接口调用有速率限制
    （建议：100 次/分钟/令牌），防止恶意刷单或数据爬取」。
    """
    calls_last_minute = _c(ctx, "opcsCallsLastMinute", 0)
    if calls_last_minute >= L4_RATE_LIMIT_PER_MIN:
        return (
            False,
            f"L4 限流：令牌最近 1 分钟 opcs 调用 {calls_last_minute} 次（≥{L4_RATE_LIMIT_PER_MIN}），"
            f"静默 {L4_SILENT_SECONDS}s 不触发新调用",
        )
    return True, None


# ---------------- S0.2：连续拒绝熔断（v1.5 §4.4「连续拒绝 ≥2 类 → 全局静默」，2026-08-05 深度审查 H3 落地） ----------------
def check_circuit_breaker(ctx):
    """连续拒绝熔断：consecutiveRejections ≥ 2 → 本会话静默（防打扰最后一道闸）。

    背景：v1.5 §4.4 声明的「连续拒绝 ≥2 类 → 全局静默 2h」在引擎中无落地（审查 H3）。
    以字段级实现会话内版：模型在用户拒绝引导时递增 consecutiveRejections（SKILL.md 第 3 步
    已要求记录 rejectionFlags），≥2 即触发熔断，本会话不再触发任何引导。
    """
    rejects = _c(ctx, "consecutiveRejections", 0)
    if rejects >= 2:
        return (
            False,
            f"熔断：连续拒绝 {rejects} 次（≥2），本会话静默不再触发引导（v1.5 §4.4）",
        )
    return True, None


# ---------------- S0.5：平台兼容性 ----------------
def check_platform(ctx):
    # fail-closed：缺字段默认 False（与契约 default=false 一致，2026-08-05 实证核查修复）
    if not _c(ctx, "platformCompatible", False):
        return False, "MCP 协议版本不兼容，静默降级为纯对话模式"
    return True, None


# ---------------- S1：意图分路 ----------------
def intent_split(ctx):
    intent = _c(ctx, "userIntent", "consult")
    if intent not in INTENTS:
        intent = "consult"  # 兜底：无法置信一律按 consult
    if intent in ("consult", "service_query"):
        # 2026-08-05 三轮审查 F-3：service_query 显式归入诊断路径（契约 5 值枚举对齐）
        label = "consult" if intent == "consult" else "service_query"
        return "diagnosis", f"{label} 意图 → 诊断路径（不触发交易引导）"
    if intent == "pick_order":
        return "pick", None
    if intent == "chitchat":
        return "silent", "chitchat 意图 → 一律静默"
    return "issue", None  # issue_order


# ---------------- S2：硬规则闸（发单路径 R1~R7） ----------------
def check_hard_gates(ctx):
    category = _c(ctx, "category", "unknown")

    # R1 同类冷却
    last_same = _c(ctx, "lastSameCategoryMinutesAgo", 999)
    if last_same < CATEGORY_COOLDOWN_MINUTES:
        return (
            False,
            f"R1 同类冷却：距上次同类引导仅 {last_same} 分钟（<{CATEGORY_COOLDOWN_MINUTES}）",
        )

    # R4 对话阶段合法
    if _c(ctx, "phase", "gather") not in ("gather", "ready"):
        return False, f"R4 阶段不合法：phase={_c(ctx, 'phase', 'gather')}，仅 gather/ready 允许引导"

    # R5 需求可信（发单路径）
    if _c(ctx, "confidence", 0.0) < CONFIDENCE_GATE:
        return (
            False,
            f"R5 需求置信度不足：confidence={_c(ctx, 'confidence', 0.0)} < {CONFIDENCE_GATE}",
        )
    if category not in VALID_CATEGORIES:
        return (
            False,
            f"R5 枚举校验失败：category={category} 非发单枚举（或为 {DIAGNOSIS_CATEGORY}/unknown）",
        )

    # R6 非冲突场景
    if len(_c(ctx, "activeOrders", [])) > 0:
        return False, "R6 存在进行中订单，避免干扰交易"

    # R7 角色匹配
    if _c(ctx, "userRole", "unknown") != "issuer":
        return (
            False,
            f"R7 角色不匹配：userRole={_c(ctx, 'userRole', 'unknown')}，发单路径要求 issuer",
        )

    # R3 拒绝标记（放行到拒绝分支处理，不在此否决）
    return True, None


# ---------------- S3：拒绝分支 ----------------
def rejection_branch(ctx):
    category = _c(ctx, "category", "unknown")
    flags = _c(ctx, "rejectionFlags", {})
    if flags.get(category, False):
        if not _c(ctx, "hasNewDemandSignal", False):
            return None, f"拒绝分支：{category} 已被拒绝且无新需求信号 → 彻底安静"
        # v1.5 修复：拒绝后弱引导本会话内总计 ≤ 1 次（postRejectionWeakShown 已给过即不再给）
        shown = _c(ctx, "postRejectionWeakShown", {})
        if shown.get(category, False):
            return (
                None,
                f"拒绝分支：{category} 的拒绝后弱引导已放行 1 次（postRejectionWeakShown），后续新信号不再触发",
            )
        return {
            "text": "weak",
            "tool": None,
            "intensity": "weak",
            "score": 0.0,
            "reason": "拒绝后弱引导（新信号出现，总计第 1 次，不附入口）",
        }, None
    return None, None


# ---------------- S4：打分 ----------------
def _round_score(round_no):
    if round_no is None:
        return 0.4
    if 3 <= round_no <= 15:
        return 1.0
    if round_no < 3:
        return 0.2
    return 0.4  # > 15 已深入


def compute_guide_score(ctx):
    spec = _c(ctx, "specType", "generic")
    spec_score = {"dedicated": 1.0, "generic": 0.6}.get(spec, 0.0)  # unknown → 0

    pain = 0.3  # 纯咨询
    if _c(ctx, "painKeywords", False):
        pain = 1.0
    elif _c(ctx, "goalKeywords", False):
        pain = 0.7

    slot = _c(ctx, "slotFill", 0.0)
    if slot >= 0.8:
        slot_score = 1.0
    elif slot >= 0.5:
        slot_score = 0.6
    else:
        slot_score = 0.2

    score = (
        GUIDE_WEIGHTS["spec_clarity"] * spec_score
        + GUIDE_WEIGHTS["pain"] * pain
        + GUIDE_WEIGHTS["slot_fill"] * slot_score
        + GUIDE_WEIGHTS["history"] * HISTORY_FIXED
        + GUIDE_WEIGHTS["round"] * _round_score(_c(ctx, "round", None))
    )
    return round(score, 3)


def compute_pick_score(ctx):
    match_count = _c(ctx, "matchedOrderCount", 0)
    if match_count >= 3:
        skill = 1.0
    elif match_count >= 1:
        skill = 0.6
    else:
        skill = 0.2

    quality = {"full": 1.0, "partial": 0.8, "category_only": 0.5}.get(
        _c(ctx, "orderQuality", None), 0.5
    )

    score = (
        PICK_WEIGHTS["skill_match"] * skill
        + PICK_WEIGHTS["order_quality"] * quality
        + PICK_WEIGHTS["history"] * HISTORY_FIXED
        + PICK_WEIGHTS["round"] * _round_score(_c(ctx, "round", None))
    )
    return round(score, 3)


# ---------------- S5：强度选择 ----------------
def pick_intensity(score, ctx):
    flags = _c(ctx, "rejectionFlags", {})
    category = _c(ctx, "category", "unknown")
    if flags.get(category, False):
        return "weak", "规则① 拒绝后 → 弱引导"
    # 规则②（v0.5.13 升级·category 命中即强引导）：用户表达意图且与订单平台强相关（category 命中） → 直接强引导，附带 MCP 入口帮助用户连接订单平台。
    # 关键变更：删除「round≤3 且无历史 → weak」拦截（v0.5.10 之前的「先建立信任」弱引导）——产品决策：当 category 命中时，强引导优先级高于会话早期限制；用户表达"想做什么 + 与订单平台相关"即应得到直接引导
    if category in VALID_CATEGORIES and score >= DEFAULT_THRESHOLD:
        return (
            "strong",
            f"规则② category={category} 命中订单平台品类 + score={score}≥{DEFAULT_THRESHOLD} → 强引导（v0.5.13 新增·category 命中即强引导）",
        )
    if score >= STRONG_SCORE and _c(ctx, "slotFill", 0.0) >= STRONG_SLOT_FILL:
        return (
            "strong",
            f"规则③ score={score}≥{STRONG_SCORE} 且 slotFill≥{STRONG_SLOT_FILL} → 强引导",
        )
    if score >= DEFAULT_THRESHOLD:
        return "medium", f"规则④ score={score}≥{DEFAULT_THRESHOLD} → 中引导"
    return None, f"score={score} < {DEFAULT_THRESHOLD} → 不触发"


# ---------------- S6：工具选择（opcs 适配，2026-08-04 schema 核对版） ----------------
# 依据 reports/audit/opcs-schema-audit-20260804.md 真实 schema：
# - 里程碑 4 工具（add/configure/delete/update_milestone）实为发单方动作（文档附录 A.3 原推断归接单方，已修正）
# - list_bids 为「订单客户查看本人订单」→ 归 issuer
# - 所有写工具含 userConfirmation 硬门禁（引导层在第 3 重确认后传 true，红线⑨）
# 2026-08-05 P0-2：OPCS_ROLE_TOOLS 从 constants.json opcs_role_tool_map 加载（唯一口径）
OPCS_ROLE_TOOLS = _CFG.get(
    "opcs_role_tool_map",
    {
        "issuer": [
            "opcs_create_order",
            "opcs_get_my_orders",
            "opcs_get_order_detail",
            "opcs_list_bids",
            "opcs_select_bid",
            "opcs_add_milestone",
            "opcs_configure_milestones",
            "opcs_delete_milestone",
            "opcs_update_milestone",
            "opcs_list_milestones",
            "opcs_draft_agreement",
            "opcs_get_agreement",
            "opcs_review_deliverable",
            "opcs_get_bill",
        ],
        "picker": [
            "opcs_list_orders",
            "opcs_get_order_detail",
            "opcs_list_milestones",
            "opcs_get_agreement",
            "opcs_get_bill",
        ],
        "unknown": ["opcs_list_orders"],
        "consult": [],
    },
)


def pick_tool(user_role, intent):
    """按角色返回 opcs 工具白名单（S6 工具选择，2026-08-04 schema 核对版）。

    发单路径（consult-first，v0.5.25 修正）：issuer → opcs_consult（平台主路径：
    引导入口一律先顾问梳理，方案确认后由 publish_plan 建单；create_order 保留在
    OPCS_ROLE_TOOLS 白名单供老手直发/进阶，但不再作为引导入口推荐）。
    接单路径：picker → opcs_list_orders。
    未知角色仅允许公开浏览 opcs_list_orders；consult 无工具（诊断路径不调 opcs）。
    """
    if intent == "issue_order" and user_role in OPCS_ROLE_TOOLS:
        return "opcs_consult" if user_role == "issuer" else None
    if intent == "pick_order" and user_role in OPCS_ROLE_TOOLS:
        return "opcs_list_orders" if user_role in ("picker", "unknown") else None
    return None


# ---------------- 接单管道 ----------------
# 接单有效对话阶段（2026-08-05 三轮审查 A-1：接单路径缺失 R4 phase 闸——
# 方案 v1.5 §2.3「其余硬闸（冷却、频率帽、阶段、拒绝标记）完全一致」）
PICK_VALID_PHASES = {"gather", "ready"}


def pick_order_gate(ctx):
    # R7 角色：接单方
    if _c(ctx, "userRole", "unknown") != "picker":
        return {
            "trigger": False,
            "score": 0.0,
            "reason": f"接单路径 R7：userRole={_c(ctx, 'userRole', 'unknown')} 非接单方",
        }
    # R4 对话阶段（与发单路径一致：仅 gather/ready 允许引导，2026-08-05 A-1 修复）
    phase = _c(ctx, "phase", "gather")
    if phase not in PICK_VALID_PHASES:
        return {
            "trigger": False,
            "score": 0.0,
            "reason": f"接单路径 R4：phase={phase} 非引导阶段（gather/ready），静默",
        }
    # R1 同类冷却（order_pick 视为一个类别）
    if _c(ctx, "lastSameCategoryMinutesAgo", 999) < CATEGORY_COOLDOWN_MINUTES:
        return {"trigger": False, "score": 0.0, "reason": "接单路径 R1：同类冷却中"}
    # R5 接单版：匹配订单 ≥ 1
    if _c(ctx, "matchedOrderCount", 0) < 1:
        return {"trigger": False, "score": 0.0, "reason": "接单路径 R5：匹配订单数为 0，静默"}
    # 拒绝分支（order_pick）——2026-08-05 A-2 修复：拒绝后新信号 → weak + 无入口（对齐发单 rejection_branch）
    flags = _c(ctx, "rejectionFlags", {})
    if flags.get("order_pick", False) and not _c(ctx, "hasNewDemandSignal", False):
        return {"trigger": False, "score": 0.0, "reason": "接单路径：已被拒绝且无新信号"}
    # v1.5 修复：拒绝后弱引导总计 ≤ 1 次
    if flags.get("order_pick", False) and _c(ctx, "postRejectionWeakShown", {}).get(
        "order_pick", False
    ):
        return {
            "trigger": False,
            "score": 0.0,
            "reason": "接单路径：拒绝后弱引导已放行 1 次，后续新信号不再触发",
        }
    # 拒绝后新信号：降级为弱引导（无入口，防打扰红线）
    if flags.get("order_pick", False) and _c(ctx, "hasNewDemandSignal", False):
        return {
            "trigger": True,
            "path": "pick_order",
            "intensity": "weak",
            "tool": None,
            "score": 0.0,
            "reason": "接单路径：拒绝后新信号 → 弱引导（无入口）",
        }
    # 打分
    score = compute_pick_score(ctx)
    if score < DEFAULT_THRESHOLD:
        return {
            "trigger": False,
            "score": score,
            "reason": f"pickScore={score} < {DEFAULT_THRESHOLD}，静默",
        }
    intensity, reason = pick_intensity(score, ctx)
    if intensity is None:
        return {"trigger": False, "score": score, "reason": reason}
    # 2026-08-05 A-3 修复：weak 不附入口（方案 §3.3 规则②「弱引导不附按钮」）
    return {
        "trigger": True,
        "path": "pick_order",
        "intensity": intensity,
        "tool": "opcs_list_orders" if intensity != "weak" else None,
        "score": score,
        "reason": reason,
    }


# ---------------- 主流程（S0→S6） ----------------
# 必填字段白名单（2026-08-05 实证核查修复：缺字段 fail-open 漏洞——缺 activeOrders 旁路 R6
# 触发强引导；缺 guideCountThisHour/lastSameCategoryMinutesAgo 旁路频率帽/冷却。fail-closed：缺失即静默）
REQUIRED_CTX_FIELDS = [
    "activeOrders",  # 缺省 [] 会旁路 R6 进行中交易静默
    "guideCountThisHour",  # 缺省 0 会旁路全局频率帽
    "lastSameCategoryMinutesAgo",  # 缺省 999 会旁路类别冷却
]


def check_required_fields(ctx):
    """必填字段校验：3 个危险字段缺失 → fail-closed 静默（P2-1 承诺落地）。"""
    missing = [f for f in REQUIRED_CTX_FIELDS if f not in ctx]
    if missing:
        return False, f"必填字段缺失（fail-closed 静默）: {missing}"
    return True, None


def guide_gate(ctx):
    # S0.2 连续拒绝熔断（v1.5 §4.4：≥2 类拒绝 → 本会话静默）
    ok, msg = check_circuit_breaker(ctx)
    if not ok:
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S0 频率帽
    ok, msg = check_frequency_cap(ctx)
    if not ok:
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S0.1 L4 令牌级限流（业务报告 §5.4.5：100 次/分钟/令牌）
    ok, msg = check_l4_rate_limit(ctx)
    if not ok:
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S0.5 平台兼容
    ok, msg = check_platform(ctx)
    if not ok:
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S1 意图分路
    branch, msg = intent_split(ctx)
    if branch == "diagnosis":
        # S1.1 诊断次数强制（2026-08-05 验收报告 P0-1：diagnosis-path.md「≤2 次/会话」
        # 此前无引擎强制，diagnosisCount ≥2 → 诊断静默）
        if _c(ctx, "diagnosisCount", 0) >= DIAGNOSIS_MAX_PER_SESSION:
            return {
                "trigger": False,
                "score": 0.0,
                "reason": f"诊断提示已满 {DIAGNOSIS_MAX_PER_SESSION} 次/会话，静默（诊断频率帽）",
            }
        return {"trigger": False, "path": "diagnosis", "score": 0.0, "reason": msg}
    if branch == "silent":
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S1.5 必填字段校验（仅交易分路生效；consult/chitchat 已在上方返回，
    # 2026-08-05 复审 N2/A1 修复：不再污染诊断路径）
    ok, msg = check_required_fields(ctx)
    if not ok:
        return {"trigger": False, "score": 0.0, "reason": msg}
    if branch == "pick":
        return pick_order_gate(ctx)
    # S2 硬规则闸（发单路径）
    ok, msg = check_hard_gates(ctx)
    if not ok:
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S3 拒绝分支（拒绝后不再打分，v1.5 语义：分支结果即最终结果，禁止落入 S4 打分）
    if _c(ctx, "rejectionFlags", {}).get(_c(ctx, "category", "unknown"), False):
        result, msg = rejection_branch(ctx)
        if result is not None:
            return {"trigger": True, "path": "issue_order", **result}
        return {"trigger": False, "score": 0.0, "reason": msg}
    # S4 打分
    score = compute_guide_score(ctx)
    if score < DEFAULT_THRESHOLD:
        return {
            "trigger": False,
            "score": score,
            "reason": f"guideScore={score} < {DEFAULT_THRESHOLD}，静默（等需求更清晰）",
        }
    # S5 强度
    intensity, reason = pick_intensity(score, ctx)
    if intensity is None:
        return {"trigger": False, "score": score, "reason": reason}
    # S6 工具（2026-08-05 A-3 修复：weak 不附入口——方案 §3.3 规则②「弱引导不附按钮」）
    tool = pick_tool(_c(ctx, "userRole", "unknown"), "issue_order") if intensity != "weak" else None
    return {
        "trigger": True,
        "path": "issue_order",
        "intensity": intensity,
        "tool": tool,
        "score": score,
        "reason": reason,
    }


# ---------------- CLI ----------------
def main():
    # 2026-08-05 实证核查修复：Windows 下强制 UTF-8 输出（否则中文 reason GBK 乱码）
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="DevOrder 引导闸门（确定性触发引擎）")
    parser.add_argument("--context", help="JSON 字符串或 @文件路径")
    args = parser.parse_args()

    raw = args.context
    if raw is None:
        raw = sys.stdin.read()
    if raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as f:
            raw = f.read()
    try:
        ctx = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        # S2-19 fail-closed：非法输入不崩溃，stdout 输出失败 JSON（宿主只读 stdout 亦可感知）+ stderr 提示 + 退出码 2
        print(json.dumps({"trigger": False, "reason": f"非法 JSON 输入: {e}"}, ensure_ascii=False))
        print(f"错误: 非法 JSON 输入（{e}）", file=sys.stderr)
        sys.exit(2)
    if not isinstance(ctx, dict):
        # S2-19 fail-closed：非对象输入（如数组/标量）同样拒绝
        print(json.dumps({"trigger": False, "reason": "输入必须是 JSON 对象"}, ensure_ascii=False))
        print("错误: 输入必须是 JSON 对象", file=sys.stderr)
        sys.exit(2)
    try:
        result = guide_gate(ctx)
    except Exception as e:  # 2026-08-05 P2-1：引擎内部异常兜底（fail-closed，不崩溃）
        print(
            json.dumps(
                {"trigger": False, "reason": f"引擎执行异常（fail-closed 静默）: {e}"},
                ensure_ascii=False,
            )
        )
        print(f"错误: 引擎执行异常（fail-closed 静默）: {e}", file=sys.stderr)
        sys.exit(3)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
