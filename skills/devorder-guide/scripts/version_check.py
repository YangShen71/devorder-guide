#!/usr/bin/env python3
"""version_check.py — 第 0 步版本检查（合并版单脚本逐行迁移 · 逻辑零改动）。

输出契约：
  GO:vX / GO:vX (network fail, continue)
  UPDATE:vY DL=... FORCE=...（检测后自动调用 update_apply.py 完成更新）
  SKIP:vX (local newer than platform vY)
  DIR_IS_BACKUP:xxx / SENTINEL_MISMATCH:loaded=A:main=B + RELOAD_HINT:<路径>
注意：版本号比较沿用原脚本的字符串比较（迁移保真，勿改语义；修复属后续 MAJOR 版）。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
import urllib.request

SKILL_DIR_OVERRIDE = None  # 测试钩子：pytest monkeypatch 注入临时目录


def _read_frontmatter_version(skill_dir: str) -> str:
    """SKILL.md frontmatter 顶层 version（与哨兵校验同一正则口径）。"""
    with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
        fm = f.read()
    m = re.search(r"^version:[ ]*([0-9]+[.][0-9]+[.][0-9]+)", fm, re.M)
    if not m:
        print("NO_VERSION_FOUND")
        raise SystemExit(2)
    return m.group(1)


def main() -> int:
    # skills_root 探测在 main()（BUG-6：测试可 monkeypatch SKILL_DIR_OVERRIDE）
    skill_dir = SKILL_DIR_OVERRIDE or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_root = os.path.dirname(os.path.normpath(skill_dir))
    version = _read_frontmatter_version(skill_dir)

    # 1) 目录健康自检
    d = os.path.basename(os.path.normpath(skill_dir))
    if d != "devorder-guide":
        print("DIR_IS_BACKUP:" + d)
        return 0
    # 2) A-1 残留清除（静默，只删私有命名空间）
    try:
        for name in os.listdir(skills_root):
            full = os.path.join(skills_root, name)
            if os.path.isdir(full) and (
                name.startswith("devorder-guide.bak-") or name.startswith("devorder-guide.old-")
            ):
                shutil.rmtree(full, ignore_errors=True)
    except Exception:
        pass
    # 3) C-3 哨兵校验（异常自愈内化，静默）
    sfile = os.path.join(skills_root, "devorder-guide.current")
    ok = False
    if os.path.exists(sfile):
        try:
            with open(sfile, encoding="utf-8") as f:
                s = json.load(f)
            cur = os.path.basename(os.path.normpath(skill_dir))
            if cur != s.get("main_dir"):
                print("SENTINEL_MISMATCH:loaded=" + cur + ":main=" + str(s.get("main_dir")))
                print("RELOAD_HINT:" + os.path.join(skills_root, str(s.get("main_dir"))))
                return 0
            v = str(s.get("version", "unknown"))
            with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
                fm = f.read()
            _m = re.search(r"^version:[ ]*([0-9]+[.][0-9]+[.][0-9]+)", fm, re.M)
            fv = _m.group(1) if _m else None
            ok = v != "unknown" and (not fv or v == fv)
        except Exception:
            ok = False
    if not ok:
        tmp = sfile + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "main_dir": "devorder-guide",
                    "version": version,
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "source": "selfheal",
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        os.replace(tmp, sfile)
    # 4) lastcheck 记录（诊断用，不再节流——2026-09-14 审计 E5 根因修复：每次加载必查网络）
    lc = os.path.join(skills_root, "devorder-guide.lastcheck")
    # 5) 网络版本查询（fail-closed 兜底）
    try:
        r = json.load(
            urllib.request.urlopen(
                urllib.request.Request(
                    "https://devorder.csdn.net/api/v1/skills/version?identity=CUSTOMER&currentVersion="
                    + version,
                    headers={"User-Agent": "devorder-guide"},
                ),
                timeout=10,
            )
        )
        d = r["data"]
        lat = d["latestVersion"]
        dl = d.get("downloadUrl", "")
        force = str(d.get("forceUpdate", False))
    except Exception:
        print("GO:v" + version + " (network fail, continue)")
        return 0
    with open(lc, "w", encoding="utf-8") as f:
        json.dump({"checked_at": time.time(), "latest": lat}, f)
    if lat == version:
        print("GO:v" + version)
    elif lat > version:
        print("UPDATE:v" + lat + " DL=" + dl + " FORCE=" + force)
        # 方案 A（2026-09-14）：自动执行更新（下载→校验→替换→收尾，update_apply.py）
        # 信号顺序保证：捕获子进程输出后按序透传（继承 stdout 会与父进程 print 缓冲乱序）
        import subprocess

        apply_py = os.path.join(skill_dir, "scripts", "update_apply.py")
        try:
            proc = subprocess.run(
                [sys.executable, apply_py, "--dl", dl, "--latest", lat, "--skill-dir", skill_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if proc.stdout:
                sys.stdout.write(proc.stdout)
                sys.stdout.flush()
        except subprocess.TimeoutExpired:
            print("UPDATE_TIMEOUT: 更新超时，保留本地旧版")
        # 更新失败不阻断（fail-closed：旧版仍可用，静默继续执行本 Skill）
        return 0
    else:
        print("SKIP:v" + version + " (local newer than platform " + lat + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
