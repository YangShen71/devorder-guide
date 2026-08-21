#!/usr/bin/env python3
"""DevOrder 质量飞轮主控 — 六位一体同步检查

用法：
    python -m src.pipeline [--check-specs] [--check-tests] [--check-impl]
                          [--check-docs] [--check-config] [--check-examples]
    python -m src.pipeline           # 运行全部检查
    python -m src.pipeline --check-specs --check-tests  # 运行指定检查

退出码：0 = 六位一体全过；1 = 任一检查失败。
"""

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS_IMPLEMENTED = ROOT / "specs" / "implemented"
SPECS_PLANNED = ROOT / "specs" / "planned"
SRC = ROOT / "src"
TESTS = ROOT / "tests"
REFERENCES = ROOT / "references"
CONFIGS = ROOT / "configs"


def _run(cmd: list[str], cwd: Path = ROOT) -> tuple[int, str, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, encoding="utf-8")
    return r.returncode, r.stdout, r.stderr


def check_specs() -> tuple[bool, list[str]]:
    """检查 specs/implemented/ 每份 Spec 的状态、锚点、边界可测性。

    精简模式（2026-08-05）：skill 运行时包已移除 specs/（开发期资产）——
    specs 目录缺失视为 N/A 通过（不阻塞运行时），存在时严格检查。
    """
    issues = []
    if not SPECS_IMPLEMENTED.exists():
        return True, ["[N/A] specs/implemented/ 不存在（精简模式，跳过 Spec 检查）"]

    spec_files = list(SPECS_IMPLEMENTED.glob("*.md"))
    if not spec_files:
        return True, ["[N/A] specs/implemented/ 下无 Spec 文件（精简模式，跳过 Spec 检查）"]

    for spec_file in spec_files:
        text = spec_file.read_text(encoding="utf-8")
        # 检查锚点（支持 `锚定:` 或 `**锚定**:` 等变体）
        if "锚定" not in text and "锚点" not in text:
            issues.append(f"{spec_file.name}: 缺少锚点标注")
        # 检查状态
        if "状态:" not in text and "**状态**" not in text:
            issues.append(f"{spec_file.name}: 缺少状态标注")
        # 检查边界可测性
        if "边界" not in text:
            issues.append(f"{spec_file.name}: 缺少边界小节")
        # 检查明确不做
        if "明确不做" not in text:
            issues.append(f"{spec_file.name}: 缺少明确不做小节")

    return len(issues) == 0, issues


def check_tests() -> tuple[bool, list[str]]:
    """运行 pytest 全量回归（开发仓库；精简模式 tests/ 缺失 → N/A 通过）。

    精简模式（2026-08-05）：skill 运行时包已移除 tests/，此时跳过 pytest
    （由 scripts/check_all.sh 的核心自检 9 场景替代）。
    """
    if not (ROOT / "tests").exists():
        return True, ["[N/A] tests/ 不存在（精简模式，跳过 pytest）"]
    code, out, err = _run([sys.executable, "-m", "pytest", "tests/unit/", "--tb=no"], cwd=ROOT)
    combined = (out or "") + (err or "")
    if code != 0:
        return False, [f"pytest 失败 (exit={code}):\n{combined[:500]}"]
    # 验证真有测试在跑：输出包含进度点或 passed
    if "." not in combined and "passed" not in combined:
        return False, ["pytest 未检测到任何测试"]
    return True, [f"pytest 通过: {combined.strip().splitlines()[-1] if combined else 'OK'}"]


def _check_opcs_whitelist(issues: list[str]) -> None:
    """OPCS 白名单一致性核对（§五 5.1：OPCS_ROLE_TOOLS 与 opcs_role_tool_map 一致）。

    guide_gate.py 的 OPCS_ROLE_TOOLS 与 configs/constants.json opcs_role_tool_map 角色键必须一致。
    """
    gate_file = SRC / "guide_gate.py"
    constants_file = CONFIGS / "constants.json"
    if not (gate_file.exists() and constants_file.exists()):
        return
    gate_text = gate_file.read_text(encoding="utf-8")
    try:
        constants = json.loads(constants_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        issues.append("configs/constants.json 解析失败（check_impl opcs 白名单核对）")
        return
    cfg_map = constants.get("opcs_role_tool_map")
    if cfg_map is None:
        return
    if "OPCS_ROLE_TOOLS" not in gate_text:
        issues.append("src/guide_gate.py 缺 OPCS_ROLE_TOOLS 常量（opcs 白名单缺失）")
        return
    import re

    m = re.search(r"OPCS_ROLE_TOOLS\s*=\s*\{([^}]*)\}", gate_text, re.S)
    if not m:
        return
    gate_keys = set(re.findall(r'"([a-z_]+)"\s*:', m.group(1)))
    cfg_keys = set(cfg_map.keys())
    if gate_keys != cfg_keys:
        issues.append(
            f"OPCS_ROLE_TOOLS 角色键 {sorted(gate_keys)} vs "
            f"constants.json {sorted(cfg_keys)} 不一致"
        )


def check_impl() -> tuple[bool, list[str]]:
    """检查 src/ 与 specs/implemented/ 的接口一致性（含 OPCS 白名单，§五 5.1）。"""
    issues = []
    spec_files = list(SPECS_IMPLEMENTED.glob("*.md")) if SPECS_IMPLEMENTED.exists() else []

    for spec_file in spec_files:
        text = spec_file.read_text(encoding="utf-8")
        # 提取锚定的源码文件（支持 `**锚定**:` 与 `**锚点**:` 格式——2026-08-05 深度审查修复：
        # 原 `"锚定:" in line` 对 `**锚定**:` 永不匹配（锚定后是 `**` 非冒号），锚点检查实际失效）
        anchors = []
        for line in text.splitlines():
            if "锚定" in line or "锚点" in line:
                # 兼容两种写法：`锚定: src/x.py` / `**锚定**: \`src/x.py\``
                body = line.split(":", 1)[-1].strip()
                parts = body.replace("`", "").split()
                anchors.extend([p for p in parts if p.endswith(".py")])

        for anchor in anchors:
            anchor_path = ROOT / anchor
            if not anchor_path.exists():
                issues.append(f"{spec_file.name}: 锚定文件 {anchor} 不存在")

    # OPCS 白名单一致性（§五 5.1：check_impl 含 OPCS_TOOLS 白名单 / opcs 工具检查）
    _check_opcs_whitelist(issues)

    # 检查 src/ 下无魔法数字（简单扫描：跳过常量区前 40 行、dict.get 默认值、引擎核心算法文件）
    seen_magic = set()
    for py_file in SRC.glob("*.py"):
        if py_file.name.startswith("_") or py_file.name == "guide_gate.py":
            continue
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            # 跳过 dict.get(x, default) 中的默认值
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "get":
                    continue
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                if node.lineno > 40 and 0 < node.value < 1:
                    key = f"{py_file.name}:{node.lineno}:{node.value}"
                    if key not in seen_magic:
                        seen_magic.add(key)
                        issues.append(
                            f"{py_file.name}:{node.lineno}: 疑似魔法数字 {node.value} "
                            f"（建议提取到 configs/constants.json）"
                        )

    return len(issues) == 0, issues


def check_docs() -> tuple[bool, list[str]]:
    """检查 references/ 文档资产完整性 + 与 tests/fixtures/templates/ 的一致性（v3.1 P-02 白名单化）。

    v3.1 修复：原实现只在"文件都存在"时才检查，任一文件缺失即静默 PASS（门禁盲区）。
    现在改为白名单校验：4 个必需文档缺失即 FAIL。
    """
    issues = []
    # 白名单：references/ 5 个必需文档（v3.0 §2.2 目录树声明 + v3.2 opcs-errors.md）
    required_docs = [
        "category-enum.md",
        "templates.md",
        "copy-constraints.md",
        "diagnosis-path.md",
        "opcs-errors.md",
    ]
    for doc in required_docs:
        if not (REFERENCES / doc).exists():
            issues.append(f"references/{doc} 缺失（v3.1 白名单必需）")

    # 检查 references/templates.md 中提到的骨架数与 tests/fixtures/templates/ 一致
    # （精简模式 2026-08-05：tests/fixtures 已移除，此检查仅在开发仓库生效）
    templates_md = REFERENCES / "templates.md"
    templates_dir = TESTS / "fixtures" / "templates"
    if templates_md.exists() and templates_dir.exists():
        md_text = templates_md.read_text(encoding="utf-8")
        json_count = len(list(templates_dir.glob("*.json")))
        # 骨架节数 = templates.md 中 "**骨架**" 出现次数（变体骨架允许多 1 个）
        skeleton_count = md_text.count("**骨架**")
        if json_count < skeleton_count:
            issues.append(
                f"references/templates.md 声明 {skeleton_count} 个骨架，"
                f"tests/fixtures/templates/ 实际 {json_count} 个 JSON"
            )

    # v0.5.24 新增（M-4）：references/ 文档阈值一致性扫描——
    # 阈值单源 = configs/constants.json（DEFAULT 0.5 / STRONG_SCORE 0.6 / STRONG_SLOT_FILL 0.65）；
    # 文档若残留旧规则文本（score≥0.65 / slotFill≥0.8 等）即 FAIL，杜绝 M-1 复发。
    import re as _re

    old_patterns = [
        (_re.compile(r"score\s*≥\s*0\.65"), "旧规则②'/④ 阈值（应为 score≥0.5）"),
        (_re.compile(r"score\s*<\s*0\.65"), "旧默认阈值（应为 score<0.5）"),
        (_re.compile(r"slotFill\s*≥\s*0\.8"), "旧规则③ slotFill 阈值（应为 0.65）"),
        (_re.compile(r"score\s*≥\s*0\.75"), "旧规则③ score 阈值（应为 0.6）"),
    ]
    for doc in REFERENCES.glob("*.md"):
        text = doc.read_text(encoding="utf-8")
        for pat, desc in old_patterns:
            m = pat.search(text)
            if m:
                line_no = text[: m.start()].count("\n") + 1
                issues.append(f"{doc.name} L{line_no} 阈值残留：{desc}（命中「{m.group(0)}」）")

    return len(issues) == 0, issues


def check_config() -> tuple[bool, list[str]]:
    """检查 configs/ 与 src/ 的常量一致性（含 opcs_role_tool_map，§五 5.1）。"""
    issues = []
    constants_json = CONFIGS / "constants.json"
    if constants_json.exists():
        try:
            constants = json.loads(constants_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            issues.append(f"configs/constants.json 解析失败: {e}")
            return False, issues

        # 检查 src/ 常量消费者（guide_gate.py + check_copy.py）与 constants.json 一致
        # （2026-08-18 Q-1 扩展：FIDELITY_* 由 check_copy.py 消费，原只查 guide_gate.py 误报）
        gate_file = SRC / "guide_gate.py"
        copy_file = SRC / "check_copy.py"
        consumer_texts = [
            f.read_text(encoding="utf-8") for f in (gate_file, copy_file) if f.exists()
        ]
        if consumer_texts:
            import re

            for key, value in constants.items():
                if isinstance(value, (int, float)):
                    # 精确匹配（2026-08-05 实证核查修复：值漂移检测；
                    # P0-2 常量单源后引擎为 `_CFG.get("KEY", value)` 形式，补 get 模式）
                    if isinstance(value, float):
                        pat = re.compile(
                            rf"\b{re.escape(key)}\s*=\s*{re.escape(str(value))}\b"
                            rf"|\b{re.escape(key)}\s*=\s*{value:g}\b"
                            rf"|\b{re.escape(key)}\s*:\s*{value:g}\b"
                            rf"|_CFG\.get\(\s*[\"']{re.escape(key)}[\"']\s*,\s*{value:g}"
                            rf"|_CFG\.get\(\s*[\"']{re.escape(key)}[\"']\s*,\s*{re.escape(str(value))}"
                        )
                    else:
                        pat = re.compile(
                            rf"\b{re.escape(key)}\s*=\s*{re.escape(str(value))}\b"
                            rf"|\b{re.escape(key)}\s*:\s*{re.escape(str(value))}\b"
                            rf"|_CFG\.get\(\s*[\"']{re.escape(key)}[\"']\s*,\s*{re.escape(str(value))}"
                        )
                    if not any(pat.search(t) for t in consumer_texts):
                        issues.append(
                            f"configs/constants.json['{key}']={value} "
                            f"在 src/（guide_gate.py/check_copy.py）中无 `{key} = {value}` 对应（值漂移或缺失）"
                        )
            # opcs_role_tool_map 一致性（§五 5.1：check_config 含 opcs_role_tool_map）
            gate_text = gate_file.read_text(encoding="utf-8") if gate_file.exists() else ""
            cfg_map = constants.get("opcs_role_tool_map")
            if cfg_map is not None:
                if "OPCS_ROLE_TOOLS" not in gate_text:
                    issues.append(
                        "src/guide_gate.py 无 OPCS_ROLE_TOOLS（opcs_role_tool_map 未接入引擎）"
                    )
    else:
        issues.append("configs/constants.json 不存在（建议创建）")

    return len(issues) == 0, issues


def check_examples() -> tuple[bool, list[str]]:
    """检查 tests/fixtures/ 与 references/ 的模板一致性（含 opcs tool 字段，§五 5.1）。

    精简模式（2026-08-05）：tests/fixtures 已移除 → N/A 通过（不阻塞运行时）。
    """
    issues = []
    contexts_dir = TESTS / "fixtures" / "contexts"
    if not contexts_dir.exists():
        return True, ["[N/A] tests/fixtures/ 不存在（精简模式，跳过 examples 检查）"]
    if len(list(contexts_dir.glob("*.json"))) < 9:
        issues.append(
            f"tests/fixtures/contexts/ 场景文件不足 "
            f"(期望 ≥9, 实际 {len(list(contexts_dir.glob('*.json')))})"
        )
    # opcs tool 字段检查（§五 5.1：check_examples 含 opcs tool 字段；🔄 v3.2 S3-19 6/6）
    templates_dir = TESTS / "fixtures" / "templates"
    if templates_dir.exists():
        missing_tool = []
        for tf in sorted(templates_dir.glob("*.json")):
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                issues.append(f"tests/fixtures/templates/{tf.name} JSON 解析失败")
                continue
            if "tool" not in data:
                missing_tool.append(tf.name)
        if missing_tool:
            issues.append(f"模板 JSON 缺 tool 字段（🔄 v3.2 S3-19 要求 6/6）: {missing_tool}")
    return len(issues) == 0, issues


CHECKS = {
    "specs": check_specs,
    "tests": check_tests,
    "impl": check_impl,
    "docs": check_docs,
    "config": check_config,
    "examples": check_examples,
}


def run(selected: list[str] | None = None) -> int:
    to_run = selected if selected else list(CHECKS.keys())
    all_ok = True
    results: list[tuple[str, bool, list[str]]] = []

    print("=" * 60)
    print("DevOrder 质量飞轮 — 六位一体同步检查")
    print("=" * 60)

    for name in to_run:
        ok, msgs = CHECKS[name]()
        results.append((name, ok, msgs))
        all_ok = all_ok and ok
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"\n[{status}] {name.upper()}")
        for msg in msgs:
            prefix = "  ✓" if ok else "  ✗"
            print(f"{prefix} {msg}")

    print("\n" + "=" * 60)
    if all_ok:
        print("结论: 六位一体全过 ✅")
        return 0
    else:
        print("结论: 存在失败项 ❌ — 禁止 merge")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="DevOrder 质量飞轮主控")
    parser.add_argument("--check-specs", action="store_true", help="检查 Spec 体系")
    parser.add_argument("--check-tests", action="store_true", help="运行 pytest 全量回归")
    parser.add_argument("--check-impl", action="store_true", help="检查实现与 Spec 一致性")
    parser.add_argument("--check-docs", action="store_true", help="检查文档一致性")
    parser.add_argument("--check-config", action="store_true", help="检查配置一致性")
    parser.add_argument("--check-examples", action="store_true", help="检查示例数据完整性")
    args = parser.parse_args()

    selected = [name for name in CHECKS.keys() if getattr(args, f"check_{name}")]
    return run(selected if selected else None)


if __name__ == "__main__":
    sys.exit(main())
