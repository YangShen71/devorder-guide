#!/usr/bin/env python3
"""评分重放验证（v3.1 P-04 / S5-21）

读取 grading.json + benchmark 数据，重放迭代评分，验证 delta 稳定。
红线②：评分修正必须历史数据重放验证（防"为通过而改评分"）。

⚠️ 开发期工具（2026-08-05 验收报告 P1-2 标注）：依赖上级目录
devorder-guide-workspace/ 的评分数据，运行时包内无该数据 → 随包运行
打印 SKIP（非错误）。评分重放验证在开发仓库执行。

用法：
    python src/grade.py iteration-1     # 重放迭代 1 评分
    python src/grade.py iteration-2     # 重放迭代 2 评分
    python src/grade.py --all           # 重放全部
退出码：0 = delta 与记录一致；1 = 不一致（禁止 merge）。
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 历史 delta 记录（实测背书，禁止篡改）
KNOWN_DELTAS = {
    "iteration-1": 0.214,  # +21.4%（迭代 1 实测）
    "iteration-2": 0.365,  # +36.5%（迭代 2 实测）
    "iteration-3": 0.365,  # +36.5%（迭代 3 实测，2026-08-07，防御路径 E12~E17）
}
DELTA_TOLERANCE = 0.005  # delta 比对容差（浮点精度）


def load_benchmark(iteration: str):
    """读取 iteration 目录下的 benchmark.json。

    数据源候选路径（2026-08-04 S5-8 验收修复）：
      ① evals/<iteration>/benchmark.json（技能包内，预留给未来内嵌评测）
      ② ../devorder-guide-workspace/<iteration>/benchmark.json（评测工作区，实测数据源）
    """
    candidates = [
        ROOT / "evals" / iteration / "benchmark.json",
        ROOT.parent / "devorder-guide-workspace" / iteration / "benchmark.json",
    ]
    for path in candidates:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return None


def compute_delta(iteration: str, benchmark: dict):
    """从 benchmark 计算 delta（pass_rate 提升或显式 delta 字段）。"""
    if "delta" in benchmark:
        return float(benchmark["delta"])
    # workspace benchmark.json 结构：run_summary.with_skill/without_skill.pass_rate.mean
    rs = benchmark.get("run_summary", {})
    with_rate = rs.get("with_skill", {}).get("pass_rate", {}).get("mean")
    without_rate = rs.get("without_skill", {}).get("pass_rate", {}).get("mean")
    if with_rate is not None and without_rate is not None:
        return round(float(with_rate) - float(without_rate), 3)
    base = float(benchmark.get("baseline_pass_rate", 0.0))
    cur = float(benchmark.get("pass_rate", 0.0))
    return round(cur - base, 3)


def content_hash(path) -> str:
    """评分数据文件哈希（纯函数验证：双跑 hash 一致）。支持 Path 或 str。"""
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def replay(iteration: str) -> int:
    """重放单个迭代：比对 delta 与 hash 稳定性。"""
    print(f"===== 评分重放: {iteration} =====")
    benchmark = load_benchmark(iteration)
    if benchmark is None:
        print(f"  [SKIP] {ROOT / 'evals' / iteration / 'benchmark.json'} 不存在（迭代未执行）")
        return 0

    delta = compute_delta(iteration, benchmark)
    expected = KNOWN_DELTAS.get(iteration)
    if expected is None:
        print(f"  [INFO] {iteration} 无历史记录，仅记录当前 delta={delta:+.1%}")
        return 0

    # 评分纯函数：聚合该迭代全部 grading.json（workspace 真实数据）双跑 hash 一致
    grading_files = list(
        (ROOT.parent / "devorder-guide-workspace" / iteration).glob(
            "eval-*/with_skill/run-*/grading.json"
        )
    )
    if not grading_files:
        grading_files = list(
            (ROOT / "evals" / iteration).glob("eval-*/with_skill/run-*/grading.json")
        )
    grading_path = grading_files[0] if grading_files else None
    if grading_path:
        # 2026-08-05 实证核查修复：原「同路径读两次恒真」无验证意义。
        # 改为仅记录 hash 作为数据指纹；数据自洽性由下方 delta 重放硬校验把关。
        h1 = content_hash(grading_path)
        print(f"  grading.json hash: {h1}（{grading_path.name}，数据指纹）")
    else:
        print("  [INFO] 未找到 grading.json（hash 检查跳过）")

    match = abs(delta - expected) < DELTA_TOLERANCE
    print(f"  delta: {delta:+.1%} vs 记录 {expected:+.1%} → {'✅ 一致' if match else '❌ 不一致'}")
    if not match:
        print("  ❌ delta 与历史记录不符 — 疑似评分被修改，禁止 merge")
        return 1
    print("  ✅ 重放通过")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="评分重放验证")
    parser.add_argument("iteration", nargs="?", help="iteration-1 / iteration-2")
    parser.add_argument("--all", action="store_true", help="重放全部")
    args = parser.parse_args()

    if args.all:
        codes = [replay(i) for i in KNOWN_DELTAS]
        return 1 if any(codes) else 0
    if args.iteration:
        return replay(args.iteration)
    print("用法: python src/grade.py iteration-1 | iteration-2 | --all")
    return 2


if __name__ == "__main__":
    sys.exit(main())
