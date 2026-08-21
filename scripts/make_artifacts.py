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


def _sync_dir(src: Path, dst: Path, excludes: set[str]) -> None:
    """镜像目录（删除 dst 中 src 没有的文件，按相对路径比对）。"""
    src_files = {f.relative_to(src) for f in src.rglob("*") if f.is_file()}
    if dst.exists():
        for f in dst.rglob("*"):
            if f.is_file() and f.relative_to(dst) not in src_files:
                f.unlink()
    for f in src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(src)
            if not any(part in excludes for part in rel.parts):  # 按路径片段排除缓存目录（f.name 对目录名无效，会把 .pyc 复制进副本）
                (dst / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst / rel)


def check_artifacts() -> list[str]:
    errors = check_mirror()
    # SKILL.md metadata.version 与 pyproject 必须一致（Release 资产与包内 frontmatter 版本同源，CI 早拦而非等 release tag 才查）
    try:
        meta = (PKG / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        meta_ver = [l.split(":", 1)[1].strip().strip('"') for l in meta.splitlines()
                    if l.strip().startswith("version")][0]
        if meta_ver != version():
            errors.append(f"SKILL.md metadata.version {meta_ver} ≠ pyproject {version()}")
    except (IndexError, KeyError):
        errors.append("SKILL.md 中找不到 metadata.version")
    if PLUGIN_DIR.exists():
        # 内容级哈希比对（第七轮修正：计划原案只比文件名集合，改内容不改名会漏检——
        # TDD 测试 test_check_detects_plugin_drift 规格即内容级，按测试实现）
        # 排除缓存目录：与 _sync_dir 的 excludes 一致——否则本地/CI 跑过 `-m src.*` 后
        # PKG/src/__pycache__ 使集合差恒非空，--check 必红（R39：CI 上 check_all 先跑必生成 __pycache__）
        def _hashes(d: Path, excludes: set[str]) -> dict[str, str]:
            out = {}
            for f in d.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(d).as_posix()
                    if not any(part in excludes for part in Path(rel).parts):
                        out[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
            return out
        truth = _hashes(PKG, {"__pycache__", ".pytest_cache", ".ruff_cache"})
        plugin = _hashes(PLUGIN_DIR, set())
        plugin.pop(".claude-plugin/plugin.json", None)   # 副本专属文件，单独校验版本
        if truth != plugin:
            errors.append("plugins/devorder-guide/ 与包内容不一致（内容级比对）")
        else:
            pj = PLUGIN_DIR / ".claude-plugin/plugin.json"
            if not pj.exists() or json.loads(pj.read_text(encoding="utf-8")).get("version") != version():
                errors.append("plugin.json 缺失或版本与 pyproject 不一致")
    for mp_path in (MARKETPLACE, ROOT / ".atomcode-plugin/marketplace.json"):
        if not mp_path.exists():
            errors.append(f"缺失 {mp_path.relative_to(ROOT)}（运行 --build）")
            continue
        try:
            mp = json.loads(mp_path.read_text(encoding="utf-8"))
            if mp.get("plugins", [{}])[0].get("version") != version():
                errors.append(f"{mp_path.relative_to(ROOT)} 版本 ≠ {version()}")
        except (json.JSONDecodeError, IndexError, KeyError):
            errors.append(f"{mp_path.relative_to(ROOT)} 无效")
    # --check 只校验「已提交状态」（镜像/双市场索引/插件副本）。dist/ 不入库，CI 全新 checkout 上必然不存在，
    # 产物存在性由 --build 末尾显式断言负责（见 build_artifacts）。
    return errors


def build_artifacts() -> None:
    build_mirror()
    # 1) LICENSE 复制进包（InsCode vendor 署名要求）
    shutil.copyfile(ROOT / "LICENSE", PKG / "LICENSE")
    # 2) plugin 副本 = 包内容 + plugin.json
    if PLUGIN_DIR.exists():
        shutil.rmtree(PLUGIN_DIR)
    _sync_dir(PKG, PLUGIN_DIR, excludes={"__pycache__", ".pytest_cache", ".ruff_cache"})
    (PLUGIN_DIR / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (PLUGIN_DIR / ".claude-plugin/plugin.json").write_text(
        json.dumps({"name": "devorder-guide", "version": version(),
                    "description": "DevOrder 对话引导 Skill（Agent Skills 标准分发版）",
                    "author": "YangShen71", "license": "Proprietary"}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    # 3) marketplace.json（入库文件，构建后需 git 提交）
    MARKETPLACE.parent.mkdir(parents=True, exist_ok=True)
    MARKETPLACE.write_text(json.dumps({
        "name": "devorder-guide-marketplace",
        "owner": {"name": "YangShen71", "email": "1690979835@qq.com"},
        "plugins": [{"name": "devorder-guide", "source": "./plugins/devorder-guide", "version": version()}],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    # 3.5) InsCode Desktop 用 AtomCode 规范目录（与 .claude-plugin 同内容，入库）——InsCode 官方市场仓实测为 .atomcode-plugin/ 前缀
    (ROOT / ".atomcode-plugin").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(MARKETPLACE, ROOT / ".atomcode-plugin/marketplace.json")
    # 4) .skill zip（复用包内打包器）
    subprocess.run([sys.executable, "-m", "src.package_skill", ".", str(DIST)],
                   cwd=PKG, check=True, env={"PYTHONUTF8": "1", **{k: v for k, v in __import__("os").environ.items()}})
    # 5) SHA256SUMS
    (DIST / "SHA256SUMS").write_text(
        f"{hashlib.sha256((DIST / 'devorder-guide.skill').read_bytes()).hexdigest()}  devorder-guide.skill\n",
        encoding="utf-8")
    for asset in ("devorder-guide.skill", "SHA256SUMS"):
        if not (DIST / asset).exists():
            raise SystemExit(f"❌ 构建后缺失产物 dist/{asset}")
    print(f"✅ 产物生成完毕：version={version()}，包大小={(DIST / 'devorder-guide.skill').stat().st_size} 字节")


def check_tag_consistency(tag: str | None) -> list[str]:
    """tag(vX.Y.Z) 与 pyproject/SKILL.md 版本必须一致。"""
    errors = []
    if not tag:
        return errors
    ver = version()
    if tag != f"v{ver}":
        errors.append(f"tag {tag} ≠ pyproject version {ver}")
    try:
        meta = (PKG / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        meta_ver = [l.split(":", 1)[1].strip().strip('"') for l in meta.splitlines()
                    if l.strip().startswith("version")][0]
        if meta_ver != ver:
            errors.append(f"SKILL.md metadata.version {meta_ver} ≠ pyproject {ver}")
    except (IndexError, KeyError):
        errors.append("SKILL.md 中找不到 metadata.version")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--build", action="store_true")
    ap.add_argument("--tag", default=None, help="git tag（vX.Y.Z），校验与包版本一致（release.yml 用）")
    args = ap.parse_args()
    if args.build:
        build_artifacts()       # 必须先 build 再 check：MIRROR 首次缺失时 check_mirror 读文件会 FileNotFoundError 崩溃（R24）
    errors = check_mirror() + check_artifacts() + check_tag_consistency(args.tag)
    if errors:
        for e in errors:
            print(f"❌ {e}")
        return 1
    print("✅ 全量一致性通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
