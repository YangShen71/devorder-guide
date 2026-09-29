#!/usr/bin/env python3
"""DevOrder 引导闸门契约审计器（v2.5 方案 §4.2 D2-5/D2-6 交付物）

静态审计 guide_gate.py，验证三条契约：
  ① score 恒有：所有含 "trigger" 键的返回 dict 必含 "score" 键
  ② 缺参清零：无 `_c(ctx, 'x')` 缺默认参数调用（防缺参崩溃）
  ③ 路径统计：返回路径总数 + 含 trigger 返回数，供人工核对覆盖完整性

含 `**展开` 的返回 dict（如主流程 `{"trigger": True, "path": ..., **result}`）
无法静态解析展开内容，列为「人工确认项」：审计者核对展开对象确实带 score。

用法：
    python audit_contract.py [path/to/guide_gate.py]

退出码：0 = 契约全过（无违规）；1 = 发现违规；2 = 文件读取/解析错误。
"""

import ast
import sys
from pathlib import Path


def audit(source: str, path: str) -> tuple[list[str], list[str], int, int]:
    """返回 (违规清单, 人工确认项清单, 返回路径总数, 含 trigger 返回数)。"""
    issues: list[str] = []
    manual: list[str] = []
    tree = ast.parse(source)
    total_returns = 0
    trigger_returns = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Return):
            continue
        total_returns += 1
        val = node.value
        if not isinstance(val, ast.Dict):
            continue

        keys = [k.value for k in val.keys if isinstance(k, ast.Constant)]
        has_star = any(k is None for k in val.keys)  # **展开的 key 为 None

        if "trigger" not in keys:
            continue
        trigger_returns += 1
        if "score" in keys:
            continue
        if has_star:
            manual.append(f"[{path}:{node.lineno}] 含 **展开，score 由展开对象提供，需人工确认")
        else:
            issues.append(f"[{path}:{node.lineno}] 返回 dict 含 trigger 但缺 score")

    # ② _c() 缺默认参数检测：调用参数 < 3（需 ctx, key, default）
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_c"
            and len(node.args) < 3
        ):
            issues.append(
                f"[{path}:{node.lineno}] _c() 缺默认参数（仅 {len(node.args)} 个实参，需 3 个）"
            )

    return issues, manual, total_returns, trigger_returns


def assert_fidelity_mode_present() -> list[str]:
    """Q-3 验收：check_copy.py 必须有 --fidelity CLI 分支"""
    # ⚠️ P0-5 修复（v1.1）：audit_contract.py 无 ROOT 定义，改用 Path(__file__) 定位仓库根
    repo_root = Path(__file__).resolve().parent.parent
    check_copy = (repo_root / "src" / "check_copy.py").read_text(encoding="utf-8")
    if "--fidelity" not in check_copy:
        return ["[FAIL] check_copy.py 缺 --fidelity 分支（Q-3 要求）"]
    return []


def assert_guide_scope_present() -> list[str]:
    """v1.5.5 验收：check_copy 首形参必须命名为 `guide`（作用域收敛）。

    首参只允许是「引导话术片段」——业务内容（顾问核心回复等）不得传入，
    否则会被计入 80 字/退路/绝对化词检查而误判。用 AST 断言形参名：
    形参名即语义契约，改名即代表作用域约定被破坏。
    """
    repo_root = Path(__file__).resolve().parent.parent
    src_path = repo_root / "src" / "check_copy.py"
    try:
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        return [f"[FAIL] 无法解析 check_copy.py：{e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "check_copy":
            args = node.args.posonlyargs + node.args.args
            if not args:
                return ["[FAIL] check_copy 无位置参数（预期首参为 `guide`）"]
            first = args[0].arg
            if first != "guide":
                return [
                    f"[FAIL] check_copy 首形参名为 `{first}`，预期 `guide`"
                    "（v1.5.5 作用域收敛：首参只允许是引导话术片段）"
                ]
            return []
    return ["[FAIL] check_copy.py 未找到 check_copy 函数定义"]


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "src/guide_gate.py"
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"[ERROR] 无法读取 {path}: {e}")
        return 2

    try:
        issues, manual, total_returns, trigger_returns = audit(source, path)
    except SyntaxError as e:
        print(f"[ERROR] 解析失败 {path}: {e}")
        return 2

    print(f"=== 契约审计报告: {path} ===")
    print(f"返回路径总数: {total_returns} | 含 trigger 返回: {trigger_returns}")
    print(f"违规项: {len(issues)} | 人工确认项: {len(manual)}")

    # Q-3 追加：check_copy.py --fidelity 存在性断言（2026-08-18 P2-4）
    q3_issues = assert_fidelity_mode_present()
    if q3_issues:
        issues.extend(q3_issues)
        print("\n[FAIL] Q-3 fidelity 断言:")
        for item in q3_issues:
            print(f"  ✗ {item}")

    # v1.5.5 追加：check_copy 作用域收敛断言（首形参 == guide）
    scope_issues = assert_guide_scope_present()
    if scope_issues:
        issues.extend(scope_issues)
        print("\n[FAIL] v1.5.5 作用域断言:")
        for item in scope_issues:
            print(f"  ✗ {item}")

    if issues:
        print("\n[FAIL] 违规清单:")
        for item in issues:
            print(f"  ✗ {item}")
        print("\n结论: 契约违反，禁止进入下一阶段。")
        return 1

    if manual:
        print("\n[INFO] 人工确认项（静态无法解析的 **展开）:")
        for item in manual:
            print(f"  ? {item}")
        print("  请核对展开对象确实携带 score 键。")

    print("\n结论: 契约全过（score 恒有 + 无缺参）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
