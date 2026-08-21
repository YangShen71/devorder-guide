#!/usr/bin/env python3
"""devorder-guide 分发产物生成器与一致性守卫（v1）。

用法:
  python scripts/make_artifacts.py --check   # 只校验，不写文件（CI 门禁）
  python scripts/make_artifacts.py --build   # 生成全部产物（Release 用）
退出码: 0 = 通过/生成成功；1 = 校验失败或构建错误。
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "skills/devorder-guide"
MIRROR = ROOT / "SKILL.md"
PLUGIN_DIR = ROOT / "plugins/devorder-guide"
MARKETPLACE = ROOT / ".claude-plugin/marketplace.json"
DIST = ROOT / "dist"


def version() -> str:
    """版本唯一真源：pyproject.toml（正则解析——tomllib 需 Python 3.11+，违反 ≥3.10 约束）。"""
    import re
    text = (PKG / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise SystemExit("pyproject.toml 中找不到 version")
    return m.group(1)


def check_mirror() -> list[str]:
    errors = []
    truth = (PKG / "SKILL.md").read_bytes()
    mirror = MIRROR.read_bytes()
    if mirror != truth:
        errors.append("根 SKILL.md 与 skills/devorder-guide/SKILL.md 不一致（运行 --build 同步）")
    return errors


def build_mirror() -> None:
    shutil.copyfile(PKG / "SKILL.md", MIRROR)
    print(f"✅ SKILL.md 镜像已同步（{MIRROR}）")


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--build", action="store_true")
    args = ap.parse_args()
    if args.build:
        build_mirror()          # 必须先 build 再 check：MIRROR 首次缺失时 check_mirror 读文件会 FileNotFoundError 崩溃（R24）
    errors = check_mirror()
    if errors:
        for e in errors:
            print(f"❌ {e}")
        return 1
    print("✅ 镜像一致性通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
