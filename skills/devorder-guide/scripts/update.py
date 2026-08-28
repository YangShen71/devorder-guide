#!/usr/bin/env python3
"""update.py — devorder-guide 版本检查与自更新（随技能包分发，零第三方依赖）

定位：**平台线 Harness 自动更新的兜底渠道**。默认主渠道是平台线 `/api/v1/skills/version` + 服务端返回的 `downloadUrl`（生产环境给用户的稳定渠道）；本脚本仅在主渠道不可达或宿主无平台线集成时（CLI/InsCode/WorkBuddy 等）作为兜底使用。

用法：
  python scripts/update.py --check      # 只读检查（无任何写操作）
  python scripts/update.py --yes        # 执行更新（写操作，须用户显式确认）
  python scripts/update.py --rollback   # 回滚到历史遗留备份（.bak-* / .old-*）

覆盖：Claude Code（autoUpdate）/ Codex 及 40+ CLI（gh skill）/ WorkBuddy（一句话触发）/ InsCode（手动+版本检查）
双轨制：本脚本只服务开源线（GitHub/GitCode 版本号 0.x）；平台线（运营端上传 1.x）由 SKILL.md「第 0 步：执行前版本检查」段承载（约定 §6/§7 接口），两线版本号各自独立、不混比。
"""

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

OWNER, REPO = "YangShen71", "devorder-guide"
GITHUB_API = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
GITCODE_OWNER = "yangshen71"
GITCODE_VER = f"https://gitcode.com/{GITCODE_OWNER}/{REPO}/raw/main/VERSION"
ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "devorder-guide-update/1.2"}
TIMEOUT = 10


def skill_version(text: str) -> str | None:
    """从 SKILL.md frontmatter 解析版本号。双模式：
    ① 顶层 version（约定 §3 形态）优先；② metadata.version 嵌套（旧形态）兜底。
    顺序不可反：顶层优先，否则 metadata 兜底永不触发。"""
    for pat in (
        r"(?m)^version:\s*[\"']?([0-9]+(?:\.[0-9]+)*)",
        r"^metadata:\s*$.*?^\s+version:\s*[\"']?([0-9]+(?:\.[0-9]+)*)",
    ):
        m = re.search(pat, text, re.M | re.S)
        if m:
            return m.group(1)
    return None


def local_version() -> str:
    v = skill_version((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    assert v, "SKILL.md 找不到 version（顶层或 metadata.version）"
    return v


def ver_tuple(v: str) -> tuple:
    """语义化版本 → int 元组。必须转 int：字符串比较会把 0.10.0 误判小于 0.9.0。"""
    m = re.match(r"(\d+(?:\.\d+)*)", v or "")
    return tuple(int(p) for p in m.group(1).split(".")) if m else (0,)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def remote_version() -> tuple | None:
    """双源取远端版本，返回 (version, source)；全失败返回 None。"""
    try:
        data = json.loads(fetch(GITHUB_API))
        return data["tag_name"].lstrip("v"), "github"
    except Exception:
        pass
    try:
        return fetch(GITCODE_VER).strip(), "gitcode"
    except Exception:
        return None


def _sha256_ok(zip_path: Path, sums: str) -> bool:
    expect = None
    for line in sums.splitlines():
        if line.strip().endswith("devorder-guide.skill"):
            expect = line.split()[0].lower()
    if not expect:
        return False
    actual = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return actual == expect


def do_update() -> int:
    remote = remote_version()
    if remote is None:
        print(
            "⚠️ 检查失败（GitHub 与 GitCode 均不可达），当前保持 v"
            + local_version()
            + "，可稍后重试或手动下载 Release zip"
        )
        return 1
    rv, src = remote
    lv = local_version()
    # 跨线检测：本地 1.x（平台线）vs 远端 0.x（开源线）→ 提示不适用，防误报「已是最新」
    if ver_tuple(lv) >= (1, 0) and ver_tuple(rv) < (1, 0):
        print(
            f"ℹ️ 本地为平台线版本 v{lv}，开源线检查不适用（平台线更新见 SKILL.md「第 0 步：执行前版本检查」段）"
        )
        return 0
    if ver_tuple(rv) <= ver_tuple(lv):
        print(f"✅ 已是最新：本地 v{lv} / 远端 v{rv}（源：{src}）")
        return 0
    print(f"ℹ️ 发现新版：本地 v{lv} → 远端 v{rv}（源：{src}）")
    if "--yes" not in sys.argv:
        print(
            "ℹ️ 这是只读检查。确认更新请执行：python scripts/update.py --yes（将下载、校验并原子替换）"
        )
        return 0
    if not os.access(ROOT, os.W_OK):
        print("❌ 技能目录不可写（本环境不支持自动更新），请手动下载 Release zip 覆盖安装")
        return 0
    try:
        api = json.loads(fetch(GITHUB_API))
        url_zip = url_sum = None
        for a in api.get("assets", []):
            if a["name"] == "devorder-guide.skill":
                url_zip = a["browser_download_url"]
            if a["name"] == "SHA256SUMS":
                url_sum = a["browser_download_url"]
        if not url_zip or not url_sum:
            print("❌ Release 资产不完整（缺 .skill 或 SHA256SUMS），中止更新")
            return 1
        tmp = Path(tempfile.mkdtemp(prefix="devorder-guide-update-"))
        try:
            zip_path = tmp / "devorder-guide.skill"
            zip_path.write_bytes(
                urllib.request.urlopen(
                    urllib.request.Request(url_zip, headers=UA), timeout=TIMEOUT
                ).read()
            )
            sums = fetch(url_sum)
            if not _sha256_ok(zip_path, sums):
                print("❌ SHA256 校验失败（下载内容被篡改或损坏），中止更新")
                return 1
            extract = tmp / "pkg"
            with zipfile.ZipFile(zip_path) as z:
                for name in z.namelist():
                    if name.endswith("/"):
                        continue
                    parts = Path(name).parts
                    if any(p == ".." for p in parts) or Path(name).is_absolute():
                        print(f"❌ Zip Slip 拦截：{name}")
                        return 1
                    target = extract.joinpath(*parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(name))
            pkg_skill = extract / "SKILL.md"
            if not pkg_skill.exists():
                print("❌ 新包缺 SKILL.md，中止更新")
                return 1
            pkg_v = skill_version(pkg_skill.read_text(encoding="utf-8"))
            if pkg_v != rv:
                print(f"❌ 新包版本校验失败（新包 v{pkg_v} ≠ 远端 v{rv}），中止更新")
                return 1
            for key in (
                "src/guide_gate.py",
                "configs/constants.json",
                "references/category-enum.md",
                "scripts/update.py",
            ):
                if not (extract / key).exists():
                    print(f"❌ 新包缺关键文件 {key}，中止更新")
                    return 1
            trash = ROOT.parent.parent / "skill-backups" / f"{ROOT.name}.old-{lv}-{int(time.time())}"
            trash.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(ROOT), str(trash))
            try:
                shutil.move(str(extract), str(ROOT))
            except Exception as e:
                try:
                    shutil.move(str(trash), str(ROOT))
                    print(f"❌ 替换失败（{e}），已回滚旧版")
                except Exception:
                    print(f"❌ 替换失败且回滚失败：技能目录现位于 {trash}，请手动恢复")
                return 1
            # 成功后删除旧版（替代而非备份）+ 清理历史遗留 .bak/.old 目录
            shutil.rmtree(str(trash), ignore_errors=True)
            # A-1 对齐：双目录扫描（skills 目录 + skill-backups 目录）
            for base in (ROOT.parent, trash.parent):
                for old in list(base.glob(f"{ROOT.name}.bak-*")) + list(base.glob(f"{ROOT.name}.old-*")):
                    shutil.rmtree(str(old), ignore_errors=True)
            # A-2 对齐：唯一主目录断言（白名单匹配——只认主目录 + .bak-*/.old-* 命名空间）
            remaining = [p.name for p in ROOT.parent.iterdir()
                         if p.is_dir() and (p.name == ROOT.name
                                            or p.name.startswith(f"{ROOT.name}.bak-")
                                            or p.name.startswith(f"{ROOT.name}.old-"))]
            if remaining != [ROOT.name]:
                print(f"⚠️ 唯一主目录断言失败，残留：{remaining}，请手工清理")
            # C-2 对齐：原子写哨兵作为更新提交点
            sentinel = ROOT.parent / "devorder-guide.current"
            sentinel_tmp = ROOT.parent / "devorder-guide.current.tmp"
            sentinel_tmp.write_text(json.dumps({
                "main_dir": ROOT.name,
                "version": rv,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "source": "opensource",
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(str(sentinel_tmp), str(sentinel))
            print(f"✅ 已更新至 v{rv}（旧版已删除替代；源：{src}）")
            return 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        print(f"⚠️ 更新失败：{e}；当前保持 v{lv}，可稍后重试或手动下载 Release zip")
        return 1


def _bak_sort_key(p: Path) -> tuple:
    """备份目录排序键：版本号（int 元组）+ 时间戳。

    必须按 basename 解析版本号而非完整路径字典序：跨目录（skills vs skill-backups）
    时父目录名会干扰排序；且字符串比较会把 1.4.10 误判小于 1.4.2。
    兼容 .bak-*（历史遗留）与 .old-*（更新失败残留）两种前缀。
    """
    m = re.match(rf"{ROOT.name}\.(?:bak|old)-([0-9.]+)(?:-(\d+))?", p.name)
    if not m:
        return ((0,), 0)
    return (ver_tuple(m.group(1)), int(m.group(2)) if m.group(2) else 0)


def do_rollback() -> int:
    # 扫两处（skills 目录 + skill-backups/）的 .bak-*（历史遗留）与 .old-*（失败残留）
    # 注：v1.4.7 起更新采用「删除替代」，正常更新成功后不留备份，此功能仅用于
    # 历史遗留 .bak 或异常中断残留 .old 的手动恢复。
    candidates = list(ROOT.parent.glob(f"{ROOT.name}.bak-*"))
    candidates += list(ROOT.parent.glob(f"{ROOT.name}.old-*"))
    candidates += list((ROOT.parent.parent / "skill-backups").glob(f"{ROOT.name}.bak-*"))
    candidates += list((ROOT.parent.parent / "skill-backups").glob(f"{ROOT.name}.old-*"))
    baks = sorted(candidates, key=_bak_sort_key)
    if not baks:
        print("ℹ️ 无可用备份，无法回滚")
        return 0
    latest = baks[-1]
    swap = ROOT.with_name(f"{ROOT.name}.swap-{int(time.time())}")
    shutil.move(str(ROOT), str(swap))
    try:
        shutil.move(str(latest), str(ROOT))
        shutil.rmtree(swap, ignore_errors=True)
    except Exception as e:
        shutil.move(str(swap), str(ROOT))
        print(f"❌ 回滚失败（{e}），已恢复当前版本")
        return 1
    print(f"✅ 已回滚（备份 {latest.name} 已恢复）；当前版本 v{local_version()}")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if cmd == "--rollback":
        return do_rollback()
    return do_update()


if __name__ == "__main__":
    sys.exit(main())
