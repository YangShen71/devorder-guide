#!/usr/bin/env python3
"""update_apply.py — DevOrder 平台线自动更新执行器（下载 → 校验 → 替换 → 收尾三件套）。

方案 A 固化（2026-09-14）：version_check.py 检测到 UPDATE 时自动调用本脚本，
结束「检测与执行分离、执行层无脚本」的设计缺口（DEVORDER-AUDIT-2026-09-14）。

用法：python update_apply.py --dl <downloadPath> --latest <latestVersion> [--skill-dir <dir>]
信号契约（与 v1.4.16 detail 内联脚本逐字节一致 + 新增网络/超时/用法信号）：
  ZIP_SLIP / NO_SKILL_MD / VERSION_MISMATCH / ROLLBACK_OK / ROLLBACK_FAILED
  UNIQUE_OK / UNIQUE_VIOLATION:<列表> / UPDATED_OK / UPDATED_TO:<vY> / RELOAD_REQUIRED
  NETWORK_FAIL / INTERNAL_ERROR / UPDATE_TIMEOUT / USAGE_ERROR
安全：ZIP_SLIP 路径穿越防护 / 版本校验 == LATEST / 就地替换（备份到 skill-backups + 就地清空 + 可靠回滚）/
      任一失败不破坏本地旧版（fail-closed）。
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile

BASE = "https://devorder.csdn.net"
UA = {"User-Agent": "devorder-guide"}


def _read_version(skill_dir: str) -> str:
    with open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines[:12]:
        if line.startswith("version:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return ""


def _clear_contents(d: str) -> None:
    """清空目录内容但保留根目录本身。

    规避 Windows 特性：进程 cwd 若位于某目录内，该目录句柄被锁定，
    os.rename / os.rmdir 该目录会抛 PermissionError(WinError 32)——
    但删除其内部子项不受影响。故「就地替换」只清内容、不删根目录。
    """
    for entry in os.scandir(d):
        if entry.is_dir(follow_symlinks=False):
            shutil.rmtree(entry.path)
        else:
            try:
                os.unlink(entry.path)
            except FileNotFoundError:
                pass


def main() -> int:
    dl = None
    latest = None
    skill_dir = None
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--dl" and i + 1 < len(argv):
            dl = argv[i + 1]
            i += 2
        elif argv[i] == "--latest" and i + 1 < len(argv):
            latest = argv[i + 1]
            i += 2
        elif argv[i] == "--skill-dir" and i + 1 < len(argv):
            skill_dir = argv[i + 1]
            i += 2
        else:
            i += 1
    if not dl or not latest:
        print("USAGE_ERROR: 需 --dl 与 --latest")
        return 2

    skill_dir = skill_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # abspath：chdir 后相对路径会失效，此处先固化为绝对路径，保证后续操作均基于绝对路径。
    skill_dir = os.path.abspath(os.path.normpath(skill_dir))
    # 规避 Windows cwd 锁定：更新会就地替换 skill_dir 内容，进程 cwd 必须移出该目录，
    # 否则 os.rename / os.rmdir 目录会失败（WinError 32）。切到系统临时目录（绝对路径）
    # 后，下方所有文件操作均用绝对路径，不受 cwd 影响。
    try:
        os.chdir(tempfile.gettempdir())
    except OSError:
        pass
    old_ver = _read_version(skill_dir)

    # 1) 下载（dl 为平台返回路径时拼 BASE；若平台返回完整 URL 则原样使用）
    url = dl if dl.startswith("http") else BASE + dl
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    except Exception:
        print("NETWORK_FAIL: 下载失败，保留本地旧版")
        return 1

    # 2) ZIP_SLIP 防护 + 解压
    try:
        with tempfile.TemporaryDirectory() as d:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for n in zf.namelist():
                    parts = n.replace("\\", "/").split("/")
                    if ".." in parts or n.startswith("/"):
                        print("ZIP_SLIP")
                        return 1
                zf.extractall(d)
            # 3) 定位新包内 SKILL.md（扁平 / 外层目录双兼容）
            pkg = None
            for root, _dirs, files in os.walk(d):
                if "SKILL.md" in files:
                    pkg = root
                    break
            if not pkg:
                print("NO_SKILL_MD")
                return 1
            # 4) 版本校验 == LATEST
            if _read_version(pkg) != latest:
                print("VERSION_MISMATCH")
                return 1
            # 5) 就地替换（2026-09-14 二次事故修复）：三段式 move（move 旧版→move 新目录）在
            #    Windows 上因进程 cwd 锁定 skill_dir 目录导致 os.rename 失败，shutil.move 静默
            #    回退 copytree+rmtree——rmtree 删光目录内容却删不掉根目录，最终旧版被「复制走+
            #    原目录清空」且回滚 move(trash, skill_dir) 因目标非空同样失败。
            #    改为「完整备份→就地清空→就地复制」+ 可靠回滚，全程不移动/删除 skill_dir 根目录。
            session_file = os.path.join(skill_dir, "devorder-guide.session.json")
            session_data = None
            if os.path.exists(session_file):
                with open(session_file, encoding="utf-8") as f:
                    session_data = f.read()
            skills_root = os.path.dirname(skill_dir)
            trash_root = os.path.join(os.path.dirname(skills_root), "skill-backups")
            os.makedirs(trash_root, exist_ok=True)
            ts = f"{int(time.time() * 1000)}-{os.getpid()}"
            trash = os.path.join(trash_root, f"devorder-guide.old-{old_ver}-{ts}")
            if os.path.exists(trash):
                shutil.rmtree(trash, ignore_errors=True)
            # 5a) 完整备份旧版（copytree 只读复制，不受 cwd 锁定影响；排除可再生缓存避免读锁）
            shutil.copytree(skill_dir, trash, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            # 5b) 就地替换（清空 → 复制新包 → 恢复会话状态）+ 失败可靠回滚
            try:
                _clear_contents(skill_dir)
                shutil.copytree(pkg, skill_dir, dirs_exist_ok=True)
                if session_data is not None:
                    with open(session_file, "w", encoding="utf-8") as f:
                        f.write(session_data)
            except Exception:
                try:
                    _clear_contents(skill_dir)
                    shutil.copytree(trash, skill_dir, dirs_exist_ok=True)
                    shutil.rmtree(trash, ignore_errors=True)
                    print("ROLLBACK_OK")
                except Exception:
                    print("ROLLBACK_FAILED: 自动回滚失败，旧版完整备份位于 " + trash)
                return 1
            # 6) 成功后删除备份 + 清理历史 .bak/.old（唯一主目录）
            shutil.rmtree(trash, ignore_errors=True)
            for old in os.listdir(trash_root):
                if old.startswith("devorder-guide.bak-") or old.startswith("devorder-guide.old-"):
                    shutil.rmtree(os.path.join(trash_root, old), ignore_errors=True)
            # 7) 收尾三件套：断言 → 哨兵 → 信号
            matches = []
            for name in os.listdir(skills_root):
                full = os.path.join(skills_root, name)
                if os.path.isdir(full) and (
                    name == "devorder-guide"
                    or name.startswith("devorder-guide.bak-")
                    or name.startswith("devorder-guide.old-")
                ):
                    matches.append(name)
            if matches != ["devorder-guide"]:
                print("UNIQUE_VIOLATION:" + ",".join(sorted(matches)))
            else:
                print("UNIQUE_OK")
            sentinel = os.path.join(skills_root, "devorder-guide.current")
            tmp = sentinel + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "main_dir": "devorder-guide",
                        "version": latest,
                        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "source": "platform",
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(tmp, sentinel)
            print("UPDATED_OK")
            print("UPDATED_TO:" + latest)
            print("RELOAD_REQUIRED")
            return 0
    except Exception:
        print("INTERNAL_ERROR: 更新流程异常，保留本地旧版")
        return 1


if __name__ == "__main__":
    sys.exit(main())
