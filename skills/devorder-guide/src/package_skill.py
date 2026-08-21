#!/usr/bin/env python3
"""Skill 打包器（v3.1 P-03 / S7-3）

将 devorder-guide 目录打包为可分发的 .skill（zip）文件，含 SKILL.md + references + src + configs + evals。
用法：python src/package_skill.py <skill-folder> [输出目录]
退出码：0 = 打包成功；1 = 校验失败。
"""

import argparse
import sys
import zipfile
from pathlib import Path

REQUIRED_TOP = {"SKILL.md", "AGENTS.md", "pyproject.toml"}
REQUIRED_REFERENCES = {
    "category-enum.md",
    "templates.md",
    "copy-constraints.md",
    "diagnosis-path.md",
    "opcs-errors.md",
}
REQUIRED_CONFIGS = {"constants.json", "contract.json"}
REQUIRED_SRC = {"guide_gate.py", "check_copy.py", "audit_contract.py", "pipeline.py"}


def validate(skill_dir: Path) -> list[str]:
    """校验技能包结构，返回问题清单（空 = 通过）。"""
    issues = []
    for f in REQUIRED_TOP:
        if not (skill_dir / f).exists():
            issues.append(f"缺失 {f}")
    refs = skill_dir / "references"
    for f in REQUIRED_REFERENCES:
        if not (refs / f).exists():
            issues.append(f"缺失 references/{f}")
    cfgs = skill_dir / "configs"
    for f in REQUIRED_CONFIGS:
        if not (cfgs / f).exists():
            issues.append(f"缺失 configs/{f}")
    src = skill_dir / "src"
    for f in REQUIRED_SRC:
        if not (src / f).exists():
            issues.append(f"缺失 src/{f}")
    # frontmatter 有效性
    sk = skill_dir / "SKILL.md"
    if sk.exists():
        head = sk.read_text(encoding="utf-8")[:200]
        if "name:" not in head or "description:" not in head:
            issues.append("SKILL.md frontmatter 无效（缺 name/description）")
    # 无残留占位符
    sk_text = sk.read_text(encoding="utf-8") if sk.exists() else ""
    if "quick_create_order" in sk_text or "quick_browse_orders" in sk_text:
        issues.append("SKILL.md 残留 quick_* 占位符（应迁移 opcs_*）")
    return issues


def package(skill_dir: Path, out_dir: Path) -> Path:
    """打包为 .skill（zip）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    name = skill_dir.name
    target = out_dir / f"{name}.skill"
    excluded = {".pytest_cache", "__pycache__", "dist", ".git", ".ruff_cache", "tests"}
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(skill_dir.rglob("*")):
            rel = p.relative_to(skill_dir)
            # 2026-08-05 实证核查修复：排除日志/临时文件（.vf2.log 泄漏教训）
            if rel.name.endswith(".log") or rel.name.endswith(".tmp"):
                continue
            if p.is_file() and not any(part in excluded for part in rel.parts):
                zf.write(p, rel)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="devorder-guide Skill 打包器")
    parser.add_argument("skill_folder", help="技能目录路径")
    parser.add_argument("out_dir", nargs="?", default="dist", help="输出目录（默认 dist）")
    args = parser.parse_args()

    skill_dir = Path(args.skill_folder).resolve()
    if not skill_dir.is_dir():
        print(f"[ERROR] 目录不存在: {skill_dir}")
        return 2

    issues = validate(skill_dir)
    if issues:
        print("❌ 校验失败（禁止打包）：")
        for i in issues:
            print(f"  - {i}")
        return 1

    target = package(skill_dir, Path(args.out_dir).resolve())
    print(f"✅ 打包成功: {target}（{target.stat().st_size} 字节）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
