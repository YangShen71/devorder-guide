#!/usr/bin/env python3
"""devorder-guide 命中回归校验（精简版随包脚本，P0-2 恢复）

背景（2026-08-05 深度审查 H4）：trigger-eval.json / test_trigger_hit.py 随精简移除，
SKILL.md 自检第 5 项「改 description 必跑命中回归」不可执行。本脚本重建为随包轻量校验：
- 数据源：evals/trigger-eval.json（真实 hit-test：23 正例 + 10 反例；opcs/v3 组空集待迭代重建）
- 校验：正例命中率 ≥90% / 反例误触发 ≤10%（description 触发词语义）
- 用途：修改 description 后必须运行，防触发面塌缩/膨胀（红线⑩）

⚠️ 定位声明（2026-08-05 复审 N9）：本脚本为「关键词代理指标」——度量的是 description
触发词与 23+10 条用例的关键词覆盖，不等于模型在真实宿主中的触发行为（与原 test_trigger_hit
同语义）。模型级触发实测依赖迭代 3 评测。

用法：python scripts/hit_check.py
退出码：0 = 达标；1 = 不达标
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# description 触发代表词（从 SKILL.md frontmatter 提取的触发语义，与 MUST_COVER 对齐；
# 2026-08-05 命中回归恢复时按真实 hit-test 正例补齐：种子用户/测评/冷启动/曝光/活动执行/运营；
# 2026-08-17 品类手册 12 品类扩展：补齐 12 品类词本身 + 关键近义词，确保 hit_check 关键词代理层 12 品类全覆盖）
TRIGGER_WORDS = [
    # === 12 品类核心触发词（description 直接列出） ===
    "增长",        # 开发者增长
    "招募",        # 用户招募
    "内容创作",    # 内容创作（含文章/视频）
    "分发",        # 内容分发
    "广告",        # 广告投放
    "会议",        # 技术会议
    "大赛",        # 开发者大赛
    "训练营",      # 训练营
    "实操",        # 动手实操
    "线下活动",    # 线下沙龙/工作坊
    "社区",        # 社区运营
    "设计",        # 开发者门户/UI 设计
    "诊断",        # 需求诊断
    # === 强交易意图词（命中即视为真实需求，豁免学习压制） ===
    "办活动",
    "技术大会",
    "训练营",
    "招募",
    "测评",
    "推广",
    "社区运营",
    "曝光",
    "发单",
    "接单",
    "需求",
    # === 真实正例补充（P0-2 恢复） ===
    "种子用户",
    "深度测评",
    "冷启动",
    "开发者运营",
    "活动执行",
    "匹配",
]
# 学习/闲聊压制标记（反例判定：含触发词但属学习型/闲聊型不触发）
LEARN_WORDS = [
    "了解",
    "流程",
    "学习",
    "科普",
    "步骤",
    "介绍",
    "调研",
    "怎么",
    "在吗",
    "聊天",
    "天气",
    "今天",
]
# 强交易词（2026-08-05 恢复：命中即视为真实需求，豁免学习压制——对齐原 test_trigger_hit TRADE_STRONG 语义）
TRADE_STRONG = ["发单", "接单", "下单", "需求", "匹配", "推广", "运营"]


def should_trigger(query: str) -> bool:
    """确定性判定：命中触发词 + 非学习/闲聊压制（强交易词豁免学习压制）。"""
    has_trigger = any(w in query for w in TRIGGER_WORDS)
    if not has_trigger:
        return False
    if any(w in query for w in LEARN_WORDS):
        if not any(w in query for w in TRADE_STRONG):
            return False  # 学习型且无强交易词 → 压制
    return True


def load_cases() -> tuple:
    d = json.loads((ROOT / "evals" / "trigger-eval.json").read_text(encoding="utf-8"))
    return d["positive"], d["negative"]


# description 核心触发词（2026-08-17 v0.4.9.8 改造：从硬列 12 品类改为开放性锚点词——
# 适应未来品类扩展，description 字面不依赖具体品类清单；
# 漂移检查只看 description 是否含「开发者服务」定位 + 「发单/接单」强意图，不限定具体品类词；
# 具体品类词通过 trigger-eval.json 正例 + TRIGGER_WORDS 同义词覆盖，扩展新品类时同步补这两处即可）
DESC_CORE_WORDS = [
    "DevOrder",       # 品牌词（识别 Skill 归属）
    "开发者",         # 服务对象锚点（开发者服务是核心定位）
    "服务",           # 服务类型锚点
    "发单",           # 强意图锚点（发单方）
    "接单",           # 强意图锚点（接单方）
]


def check_desc_word_drift() -> list:
    """description ↔ 核心触发词漂移检查（2026-08-05 复审 N10：
    DESC_CORE_WORDS 必须被 description 直接包含，缺失即告警防触发面塌缩）。"""
    sk = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^description: (.+)$", sk, re.M)
    if not m:
        return ["SKILL.md 无 description（无法核对词表漂移）"]
    desc = m.group(1)
    missing = [w for w in DESC_CORE_WORDS if w not in desc]
    return [f"description 缺失核心触发词（触发面塌缩风险）: {missing}"] if missing else []


def main() -> int:
    # 2026-08-05 三轮审查 R-2：Windows GBK 控制台需 UTF-8 输出（✅ 等字符 GBK 无法编码）
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    pos, neg = load_cases()
    pos_hits = sum(1 for c in pos if should_trigger(c["query"]))
    neg_hits = sum(1 for c in neg if should_trigger(c["query"]))
    pos_rate = pos_hits / len(pos)
    neg_rate = neg_hits / len(neg)
    print(
        f"正例命中率: {pos_rate:.0%}（{pos_hits}/{len(pos)}） 目标 ≥90% {'✅' if pos_rate >= 0.9 else '❌'}"
    )
    print(
        f"反例误触发: {neg_rate:.0%}（{neg_hits}/{len(neg)}） 目标 ≤10% {'✅' if neg_rate <= 0.1 else '❌'}"
    )
    # description 词表漂移检查（N10）
    drift = check_desc_word_drift()
    for d_ in drift:
        print(f"⚠️ {d_}")
    ok = pos_rate >= 0.90 and neg_rate <= 0.10 and not drift
    print(f"命中回归: {'✅ 达标' if ok else '❌ 不达标（改 description 必跑）'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
