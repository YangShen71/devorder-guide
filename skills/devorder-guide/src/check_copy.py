#!/usr/bin/env python3
"""DevOrder 引导话术合规校验器（D3-4 交付物，附录 I）

确定性校验：润色由模型完成，合规由脚本把关（v1.5 §4.1 第三道工序）。
校验失败 → 调用方回退骨架（fail-closed）。

用法：
    python check_copy.py '<polished>' '<skeleton>'   →   JSON
"""

import json
import re
import sys

ABSOLUTES = ["保证", "一定", "最快", "绝对", "肯定", "100%"]
ESCAPES = [
    "继续聊",
    "不急",
    "不着急",
    "你自己",
    "完全没问题",
    "完全可以",
    "随时找我",
    "看你怎么方便",
    "想好了再",
]
MAX_GUIDE_HANZI = 80


def hanzi_count(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text))


# 入口语义识别（2026-08-05 实证核查修复：原字面匹配「一键发单」误杀等价润色）
ENTRY_ISSUE = ["发单", "下个单", "下单", "整理成单", "帮你把需求", "把需求交给"]
ENTRY_PICK = ["接单", "看看有没有", "帮你找", "匹配到", "抢单", "查看详情"]


def _entry_type(text: str) -> str:
    """识别话术的入口类型（issue / pick / none），2026-08-05 深度审查 M3 升级：
    原布尔比对无法区分「骨架发单、润色接单」的类型漂移。"""
    has_issue = any(w in text for w in ENTRY_ISSUE)
    has_pick = any(w in text for w in ENTRY_PICK)
    if has_issue and not has_pick:
        return "issue"
    if has_pick and not has_issue:
        return "pick"
    if has_issue and has_pick:
        return "both"
    return "none"


# v0.5.15 新增 · 显式选项检测（中/强引导硬要求）
# 骨架有入口（issue/pick/both）时，润色必须含 ≥ 2 个编号选项 + 后果说明 + 快捷触发词说明。
# 骨架无入口（none，弱引导）时，不应强制选项——但若润色加了选项也不报错。
# v0.5.18 扩展：支持表格形态（| **1. 一键发单** |）——行首数字编号 或 表格单元格数字编号
OPTION_PATTERN = re.compile(r"(?:^|\n)\s*(?:\|?\s*\*?\*?)(\d+)\s*[.\、\)]\s*", re.MULTILINE)
SHORTCUT_HINTS = (
    "回复 1",
    "回复 2",
    "回复 3",
    "回复 `1`",
    "回复 `2`",
    "回复 `3`",
    "选 1",
    "选 2",
    "选 3",
    "选 `1`",
    "选 `2`",
    "选 `3`",
    "直接说",
    "回复「",
    "回复『",
    "说「",
    "说『",
)


def _has_options(text: str) -> tuple[bool, str]:
    """v0.5.15 新增 · 检测话术是否含显式选项 + 快捷触发词说明。

    v0.5.18 扩展：OPTION_PATTERN 支持表格形态（| **1. xxx** |）与编号列表（1. xxx）两种。

    Returns:
        (是否满足, 失败原因)。
    """
    # 匹配 "1." / "1)" / "**1.**" / "*1.*" / "| **1. ...** |" 等编号模式（行首或表格单元格）
    matches = OPTION_PATTERN.findall(text)
    # 去重（同一编号可能多次匹配）
    unique_nums = set(matches)
    if len(unique_nums) < 2:
        return False, f"少于 2 个编号选项（{len(unique_nums)} 处）"
    if not any(s in text for s in SHORTCUT_HINTS):
        return False, "缺快捷触发词说明（如「回复 1」「选 1」「直接说」）"
    return True, ""


def check_copy(polished: str, skeleton: str) -> dict:
    """输入润色文本与骨架，输出 pass/fail + 违规项。

    v0.5.15 新增：长度检查拆分为「核心引导句 ≤ 80 汉字 + 选项列表独立检测」；
    中/强引导（骨架有入口）必须含显式选项（≥ 2 个编号 + 快捷触发词说明）。
    """
    issues = []
    if any(w in polished for w in ABSOLUTES):
        issues.append("含绝对化词汇")
    if not any(w in polished for w in ESCAPES):
        issues.append("缺退路表达")

    # v0.5.15：长度检查拆分为「核心引导句（≤ 80 汉字）」+「选项列表（独立结构）」
    # v0.5.18：分界扩展——编号列表行（1.）或表格头行（| 选项 |）或表格单元格（| 1.）之前为核心引导句
    core_match = re.search(r"(?:^|\n)\s*(?:\|?\s*\*?\*?)(?:\d+[.\、\)]|选项|含义|动作)", polished)
    core_guide = polished[: core_match.start()] if core_match else polished
    n = hanzi_count(core_guide)
    if n > MAX_GUIDE_HANZI:
        issues.append(f"超 {MAX_GUIDE_HANZI} 汉字（核心引导句 {n} 字，不含选项列表）")

    skel_entry = _entry_type(skeleton)
    pol_entry = _entry_type(polished)
    # 类型比对（2026-08-05 深度审查 M3：布尔比对无法区分发单/接单类型漂移；
    # M-4 收紧：骨架 both 时润色必须 both，不允许收敛为单一路径）
    if skel_entry == "none" and pol_entry != "none":
        issues.append("骨架无入口，润色不得加入口")
    elif skel_entry != "none" and pol_entry == "none":
        issues.append("骨架有入口，润色不得丢失")
    elif skel_entry == "both" and pol_entry != "both":
        issues.append(f"骨架双入口，润色不得收敛为单一（骨架=both，润色={pol_entry}）")
    elif skel_entry in ("issue", "pick") and pol_entry not in (skel_entry, "both"):
        issues.append(f"入口类型不一致（骨架={skel_entry}，润色={pol_entry}）")

    # v0.5.15 新增：中/强引导（骨架有入口）必须含显式选项
    if skel_entry != "none":
        has_opts, reason = _has_options(polished)
        if not has_opts:
            issues.append(f"v0.5.15 缺显式选项：{reason}")

    return {"passed": not issues, "hanzi": n, "issues": issues}


def main():
    # 2026-08-05 实证核查修复：Windows 下强制 UTF-8 输出（中文违规清单不乱码）
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) >= 5 and sys.argv[1] == "--fidelity" and sys.argv[2] == "--only-numbers":
        # R-2 只过关键数字：仅校验数字，跳过长句（必须放在 --fidelity 4 参数分支之前）
        reply, relay = sys.argv[3], sys.argv[4]
        numbers = extract_business_numbers(reply)
        missing = [n for n in numbers if n not in relay]
        print(
            json.dumps(
                {"passed": not missing, "missing_numbers": missing},
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(0 if not missing else 1)
    if len(sys.argv) >= 4 and sys.argv[1] == "--fidelity":
        # 兼容两种调用：--fidelity reply relay vs 文件路径
        reply = sys.argv[2]
        relay = sys.argv[3]
        if _Path(reply).exists():
            reply = _Path(reply).read_text(encoding="utf-8")
        if _Path(relay).exists():
            relay = _Path(relay).read_text(encoding="utf-8")
        r = fidelity_check(reply, relay)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(enforce_or_warn(r))  # ⚠️ P0-4 修复（v1.1）：接入 R-1 灰度，而非强制 0/1
    if len(sys.argv) != 3:
        print(
            json.dumps(
                {"error": "用法：python check_copy.py '<polished>' '<skeleton>'"},
                ensure_ascii=False,
            )
        )
        sys.exit(2)
    print(json.dumps(check_copy(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))


# ============================================================
# v0.5.0 fidelity_check — 转达保真确定性校验
# ============================================================
# 目的：捕获宿主 LLM 转述时的数字丢失/改写（如"人均 X 元"被吞）。
# 设计：纯 Python，零 LLM 调用——可作为转达后自检的硬闸。
# 演进：阶段一（粗）→ 阶段二（中，业务数字分桶）→ 阶段三（精，函数化）。
# v5.0 上线阶段一，灰度默认 warn；阶段二/三随版本演进。

import json as _json
import re as _re
from pathlib import Path as _Path

# ⚠️ P0-3 修复（v1.1）：常量独立加载（fallback 默认值）——不依赖 P1-4 Q-1 的执行顺序。
# 若 constants.json 已含 FIDELITY_*（Q-1 落地后），此处自动读取；否则用下方默认值，不会 NameError。
_CFG_PATH = _Path(__file__).resolve().parent.parent / "configs" / "constants.json"
_CFG = _json.loads(_CFG_PATH.read_text(encoding="utf-8")) if _CFG_PATH.exists() else {}

# P1-4 Q-1 落地：FIDELITY_* 常量单一数据源（constants.json），check_copy.py 不再硬编码阈值
FIDELITY_MODE = _CFG.get("FIDELITY_MODE", "warn")  # off/warn/enforce 三档灰度
FIDELITY_MIN_PHRASE_LEN = _CFG.get("FIDELITY_MIN_PHRASE_LEN", 12)
FIDELITY_ONLY_NUMBERS_FALLBACK = _CFG.get("FIDELITY_ONLY_NUMBERS_FALLBACK", False)
FIDELITY_BLOCK_CHECK = _CFG.get("FIDELITY_BLOCK_CHECK", True)

# 阶段一正则（粗）——可作为 fallback回退
NUM_RE_V1 = _re.compile(r"¥?\s*\d[\d,\.]*\s*(?:万|元|人|个|天|名|篇|%|折)?")

# 阶段二正则（中）——按业务语境分 4 类
NUM_RE_V2 = _re.compile(
    r"(?:¥|￥)\s*\d[\d,\.]*\s*(?:万|千|百)?(?:元|块)?\s*"  # 货币
    r"|\d+\.?\d*\s*(?:%|百分比|折|扣)"  # 比率
    r"|\d[\d,\.]*\s*(?:人|名|位|个|家|场|次|篇|页|本|条|项|个用户)"  # 数量
    r"|\d[\d,\.]*\s*(?:天|日|月|年|小时|分钟|秒|周|季度)"  # 时间
)


def extract_business_numbers_v1(text: str) -> list:
    """v1 粗匹配：直接按 NUM_RE_V1 提取"""
    return NUM_RE_V1.findall(text)


def extract_business_numbers_v2(text: str) -> list:
    """v2 业务匹配：按 4 类业务数字分桶，剔除年份/序号/编号"""
    return NUM_RE_V2.findall(text)


# 默认用 v1（兼容性最高），可通过 FIDELITY_REG_VERSION 切换
REG_VERSION = _CFG.get("FIDELITY_REG_VERSION", "v1")  # v1/v2/v3
_extract_fn = {
    "v1": extract_business_numbers_v1,
    "v2": extract_business_numbers_v2,
}.get(REG_VERSION, extract_business_numbers_v1)


def extract_business_numbers(text: str) -> list:
    """提取业务数字（v0.4.9.7 数字纪律的契约级执行）"""
    return _extract_fn(text)


def fidelity_check(reply: str, relay: str) -> dict:
    """reply 原文 → 转达文本的保真比对。

    Args:
        reply: 顾问 Agent 返回的 reply 原文
        relay: 模型转达给用户的文本

    Returns:
        dict {passed, missing_numbers, missing_phrases, fidelity_rate}
        - passed: 数字 + 长句全保真（无 missing）
        - fidelity_rate: 1.0 - 缺失/总数（用于 O-1 埋点）
    """
    # R-3 feature flag：FIDELITY_BLOCK_CHECK=false 时仅校验数字，跳过长句（默认 true）
    if not _CFG.get("FIDELITY_BLOCK_CHECK", True):
        numbers = extract_business_numbers(reply)
        missing = [n for n in numbers if n not in relay]
        return {
            "passed": not missing,
            "missing_numbers": missing,
            "missing_phrases": [],
            "fidelity_rate": 1.0 if not missing else 0.0,
        }
    numbers = extract_business_numbers(reply)
    missing_numbers = [n for n in numbers if n not in relay]

    phrases = [s for s in _re.split(r"[。\n]", reply) if len(s) > FIDELITY_MIN_PHRASE_LEN]
    missing_phrases = [p for p in phrases if p not in relay]

    total = len(numbers) + len(phrases)
    missing = len(missing_numbers) + len(missing_phrases)
    fidelity_rate = round(1.0 - (missing / total), 3) if total > 0 else 1.0

    return {
        "passed": not missing_numbers and not missing_phrases,
        "missing_numbers": missing_numbers,
        "missing_phrases": missing_phrases,
        "fidelity_rate": fidelity_rate,
    }


def enforce_or_warn(r: dict) -> int:
    """R-1：按 FIDELITY_MODE 决定是否退出（off/warn 不退出，enforce 退出）"""
    mode = _CFG.get("FIDELITY_MODE", "warn")
    if r["passed"]:
        return 0
    if mode == "off":
        return 0
    if mode == "warn":
        print(f"⚠️ 保真度={r['fidelity_rate']}: missing={r['missing_numbers']}", file=sys.stderr)
        return 0
    return 1


if __name__ == "__main__":
    main()
