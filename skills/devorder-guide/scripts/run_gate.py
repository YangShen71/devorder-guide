#!/usr/bin/env python3
"""run_gate.py — 发单方闸门单条调用入口（方案甲核心 · v1.4.18）。

职责：读会话状态 -> build_ctx 单一合并点组装（内置常量 ∪ 状态累计字段 ∪ CLI 每轮字段）
      -> 调引擎 guide_gate -> main 回写累计状态 -> 原样输出 verdict JSON。
红线：不改引擎三文件；引擎源码不读入 context；输出 JSON 是判定唯一证据。
状态边界：session.json 只持久化累计字段（guideCountThisHour / rejectionFlags /
          postRejectionWeakShown / lastTriggerTs）；hasNewDemandSignal / activeOrders
          每轮独立，不持久化。
冷却语义（执行修正 R6.1）：引擎将 lastSameCategoryMinutesAgo 的 0/None 归一为 999
  （v1.4.15 首轮保护），故「写回 0」无法形成同类冷却——改为持久化 lastTriggerTs
  （{category: epoch}），下一轮按真实经过分钟计算，保证防骚扰第①层（同类冷却）语义完整。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT / "src"))

from guide_gate import guide_gate  # noqa: E402  引擎入口（实读签名 2026-09-11）

SESSION_FILE = SKILL_ROOT / "devorder-guide.session.json"

VALID_CATEGORIES = (
    "dev_growth",
    "user_acquisition",
    "event",
    "community",
    "exposure",
    "software_build",
    "content_writing",
    "video_production",
    "product_testing",
    "visual_design",
    "hardware_eng",
)
EVENT_SUBTYPES = ("conference", "competition", "camp", "live", "workshop")
SPEC_TYPES = ("dedicated", "generic", "unknown")

# 首轮安全值（危险字段：禁 0/null，见 SKILL.md 危险字段段）
SAFE_LAST_SAME_MINUTES = 999

# 内置默认（排查报告 §3.1：不暴露为 CLI 的常量）
BUILTIN = {
    "platform": "workbuddy",
    "platformCompatible": True,
    "userIntent": "issue_order",
    "userRole": "issuer",
    "phase": "gather",
    "activeOrders": [],
    "hasNewDemandSignal": False,
    "painKeywords": False,
    "guideHistory": [],
    "matchedOrderCount": 0,
    "orderQuality": None,
    "consecutiveRejections": 0,
    "opcsCallsLastMinute": 0,
}


def _fresh_state(session_id: str) -> dict:
    """首次/重置状态：4 累计字段 + lastTriggerTs，dict 值全新（不可共享引用）。"""
    return {
        "sessionId": session_id,
        "guideCountThisHour": 0,
        "rejectionFlags": {},
        "postRejectionWeakShown": {},
        "lastTriggerTs": {},
    }


def load_state(session_id: str) -> dict:
    """读会话状态；文件缺失/损坏/session-id 不匹配 -> 首次状态（防跨会话状态污染）。"""
    try:
        state = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        if state.get("sessionId") != session_id:
            return _fresh_state(session_id)
        return state
    except (OSError, json.JSONDecodeError):
        return _fresh_state(session_id)


def save_state(state: dict) -> None:
    """原子写回（tmp + replace），防写一半损坏。"""
    tmp = SESSION_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SESSION_FILE)


def _last_same_minutes(state: dict, category: str) -> int:
    """同类冷却口径：按 lastTriggerTs 计算真实经过分钟；未触发过 -> 999。"""
    last_ts = state.get("lastTriggerTs", {}).get(category)
    if not last_ts:
        return SAFE_LAST_SAME_MINUTES
    minutes = int((time.time() - float(last_ts)) / 60)
    return min(999, max(0, minutes))


def build_ctx(args: argparse.Namespace, state: dict) -> dict:
    """单一合并点（BUG-14）：内置常量 ∪ 状态累计字段 ∪ CLI 每轮字段。"""
    ctx = dict(BUILTIN)
    ctx.update(
        {
            "sessionId": args.session_id,
            "category": args.category,
            "confidence": args.confidence,
            "slotFill": args.slot_fill,
            "round": args.round,
            "goalKeywords": bool(args.goal_keywords),
            "specType": args.spec_type,
            "painKeywords": bool(args.pain_keywords),
            "phase": args.phase,
            # 累计字段（session.json 维护）
            "guideCountThisHour": state.get("guideCountThisHour", 0),
            "lastSameCategoryMinutesAgo": _last_same_minutes(state, args.category),
            "rejectionFlags": state.get("rejectionFlags", {}),
            "postRejectionWeakShown": state.get("postRejectionWeakShown", {}),
            # 每轮独立（不持久化）
            "hasNewDemandSignal": bool(args.new_signal),
            "activeOrders": [{} for _ in range(args.active_orders)] if args.active_orders else [],
        }
    )
    if args.category == "event":
        if not args.subtype:
            print('{"ok": false, "error": "event 必须传 --subtype"}', file=sys.stderr)
            raise SystemExit(2)
        ctx["subtype"] = args.subtype
    # --weak-shown：显式覆盖 postRejectionWeakShown（default=None 不覆盖，用 session 状态）。
    # 主路径 = 脚本自动写回（update_state）；本参数用于跨会话/状态丢失时显式告知「已放行过」。
    if args.weak_shown is not None:
        shown = dict(ctx["postRejectionWeakShown"])
        shown[args.category] = bool(args.weak_shown)
        ctx["postRejectionWeakShown"] = shown
    return ctx


def update_state(state: dict, verdict: dict, category: str, new_signal: bool) -> dict:
    """回写累计字段（main 回写，BUG-14）。trigger=false 不动状态。

    BUG-33：判断「拒绝后 weak 放行」用状态组合（rejectionFlags[category] + new_signal + weak），
    不依赖引擎 reason 文案。
    """
    if not verdict.get("trigger"):
        return state
    state = dict(state)
    state["guideCountThisHour"] = int(state.get("guideCountThisHour", 0)) + 1
    ts_map = dict(state.get("lastTriggerTs", {}))
    ts_map[category] = time.time()  # 同类冷却起点（R6.1：存时间戳，下一轮算真实分钟）
    state["lastTriggerTs"] = ts_map
    rejected = state.get("rejectionFlags", {}).get(category, False)
    if verdict.get("intensity") == "weak" and rejected and new_signal:
        # 拒绝后 weak 放行（总计第 1 次）-> 标记已放行（R2 语义：后续新信号不再触发）
        shown = dict(state.get("postRejectionWeakShown", {}))
        shown[category] = True
        state["postRejectionWeakShown"] = shown
    return state


def _unit_float(raw: str) -> float:
    """0~1 闭区间浮点（confidence / slotFill）。2026-09-22：补范围校验，此前 2.0/-1 被静默接受。"""
    value = float(raw)
    if not 0.0 <= value <= 1.0:
        raise argparse.ArgumentTypeError(f"需在 0~1 之间，实际 {value}")
    return value


def _non_negative_int(raw: str) -> int:
    """非负整数（--active-orders）。负数此前会让 range() 静默产出空列表。"""
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError(f"需 ≥0，实际 {value}")
    return value


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="发单方闸门单条调用（方案甲）")
    p.add_argument("--category", choices=VALID_CATEGORIES, default=None)
    p.add_argument("--subtype", choices=EVENT_SUBTYPES, default=None)
    p.add_argument("--confidence", type=_unit_float, default=None)
    p.add_argument("--slot-fill", type=_unit_float, default=None, dest="slot_fill")
    p.add_argument("--round", type=int, default=None)
    p.add_argument("--goal-keywords", type=int, choices=(0, 1), default=None, dest="goal_keywords")
    p.add_argument("--spec-type", choices=SPEC_TYPES, default=None, dest="spec_type")
    p.add_argument("--session-id", required=True, dest="session_id", help="必传，防跨会话状态污染")
    p.add_argument("--pain-keywords", type=int, choices=(0, 1), default=0, dest="pain_keywords")
    p.add_argument("--phase", choices=("gather", "ready"), default="gather")
    p.add_argument("--new-signal", type=int, choices=(0, 1), default=0, dest="new_signal")
    p.add_argument("--active-orders", type=_non_negative_int, default=0, dest="active_orders")
    p.add_argument("--weak-shown", type=int, choices=(0, 1), default=None, dest="weak_shown")
    p.add_argument("--terse", action="store_true", help="只输出 trigger/intensity/tool 三字段")
    p.add_argument(
        "--reject", choices=VALID_CATEGORIES, default=None, help="用户拒绝后记录 rejectionFlags"
    )
    p.add_argument("--reset", action="store_true", help="新会话开始重置状态")
    args = p.parse_args()

    if args.reject:
        state = load_state(args.session_id)
        flags = dict(state.get("rejectionFlags", {}))
        flags[args.reject] = True
        state["rejectionFlags"] = flags
        save_state(state)
        print(json.dumps({"ok": True, "recorded": args.reject}, ensure_ascii=False))
        return 0
    if args.reset:
        save_state(_fresh_state(args.session_id))
        print(json.dumps({"ok": True, "reset": True}, ensure_ascii=False))
        return 0

    if (
        not args.category
        or args.confidence is None
        or args.slot_fill is None
        or args.round is None
        or args.goal_keywords is None
        or args.spec_type is None
    ):
        p.error(
            "gate 模式必传: --category --confidence --slot-fill --round --goal-keywords --spec-type"
        )
    state = load_state(args.session_id)
    ctx = build_ctx(args, state)
    verdict = guide_gate(ctx)
    state = update_state(state, verdict, args.category, bool(args.new_signal))
    save_state(state)

    if args.terse:
        print(
            json.dumps(
                {k: verdict.get(k) for k in ("trigger", "intensity", "tool")}, ensure_ascii=False
            )
        )
    else:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
