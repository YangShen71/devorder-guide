#!/usr/bin/env bash
# verify_install.sh — 分发漂移防护：打包 → 安装 → 一致性复验（O-5 机制固化）
#
# 背景（2026-08-04 深度审查 P0-1）：
#   S3~S5 阶段修复（模板 tool 字段/grade.py 数据源/pipeline opcs 检查/命中测试）后
#   未重新打包安装，导致安装版与源码版 23 文件差异。本脚本固化三步一体校验。
#
# 用法：
#   bash scripts/verify_install.sh [--skip-package] [--install-dir <path>]
#
# 退出码：0 = 安装版与源码版零差异；1 = 有差异（禁止宣称"已分发"）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # 脚本移入包内后：scripts/../../.. = 仓库根（dist 产物输出目录；第七轮修正：../.. 只到 skills/）
SKIP_PACKAGE="${1:-}"
INSTALL_DIR="${2:-$HOME/.workbuddy/skills/devorder-guide}"
PYTHON="${PYTHON:-python}"

# --targets 多工具循环（子命令，置于 SKIP_PACKAGE 解析之前；通过自调用 + 既有 $2 安装目录参数复用全流程）
if [[ "${1:-}" == "--targets" ]]; then
  [[ -z "${2:-}" ]] && { echo "用法: $0 --targets claude,codex,...（工具列表不能为空）"; exit 1; }   # R41：空列表不再静默空转
  for t in ${2//,/ }; do
    case "$t" in
      claude)    D="$HOME/.claude/skills";;
      codex)     D="$HOME/.agents/skills";;
      cursor)    D="$HOME/.cursor/skills";;
      kimi)      D="$HOME/.kimi-code/skills";;
      trae-cn)   D="$HOME/.trae-cn/skills";;
      trae)      D="$HOME/.trae/skills";;
      workbuddy) D="$HOME/.workbuddy/skills";;
      *) echo "❌ 未知工具: $t"; exit 1;;
    esac
    echo "── 工具 $t → ${D}/devorder-guide ──"
    bash "$0" "" "${D}/devorder-guide"     # 复用既有全流程（$1 空=完整流程，$2=安装目录）
  done
  exit 0
fi

# --temp-install 模式（CI/临时验收用：解压到临时目录，退出自动清理；覆盖 INSTALL_DIR）
TEMP_INSTALL=""
case "${1:-}" in
  --temp-install) TEMP_INSTALL=1;;
esac
if [[ -n "${TEMP_INSTALL}" ]]; then
  INSTALL_DIR="$(mktemp -d)/devorder-guide"
  trap 'rm -rf "$(dirname "${INSTALL_DIR}")"' EXIT
fi

# Git Bash 路径 → Windows 路径（Python 需要）
if command -v cygpath >/dev/null 2>&1; then
  ROOT_WIN="$(cygpath -w "${ROOT}")"
  INSTALL_WIN="$(cygpath -w "${INSTALL_DIR}")"
  SKILL_ZIP_WIN="$(cygpath -w "${REPO_ROOT}/dist/devorder-guide.skill")"
else
  ROOT_WIN="${ROOT}"; INSTALL_WIN="${INSTALL_DIR}"; SKILL_ZIP_WIN="${REPO_ROOT}/dist/devorder-guide.skill"   # Linux/CI 无 cygpath 回退：产物在仓库根 dist/（与打包输出同目录，防同款路径漂移）
fi

echo "=== O-5 分发漂移防护校验 ==="
echo "源码根: ${ROOT}"
echo "安装目录: ${INSTALL_DIR}"

# 1) 打包（可跳过，用于已打包/复验场景）
if [[ "${SKIP_PACKAGE}" != "--skip-package" ]]; then
  echo ""
  echo "[1/4] 重新打包 .skill ..."
  (cd "${ROOT}" && PYTHONUTF8=1 "${PYTHON}" -m src.package_skill . "${REPO_ROOT}/dist")

  echo ""
  echo "[2/4] 版本核对（H-3：防装错版本零差异通过）..."
  SRC_VER=$("${PYTHON}" -c "
import re
text = open(r'${ROOT_WIN}/SKILL.md', encoding='utf-8').read()
m = re.search(r'version:\s*[\"\']?([0-9]+\.[0-9]+\.[0-9]+)', text)
print(m.group(1) if m else 'UNKNOWN')
")
  PKG_VER=$("${PYTHON}" -c "
import zipfile, re
z = zipfile.ZipFile(r'${SKILL_ZIP_WIN}')
text = z.read('SKILL.md').decode('utf-8')
m = re.search(r'version:\s*[\"\']?([0-9]+\.[0-9]+\.[0-9]+)', text)
print(m.group(1) if m else 'UNKNOWN')
")
  PYPROJ_VER=$("${PYTHON}" -c "
import re
text = open(r'${ROOT_WIN}/pyproject.toml', encoding='utf-8').read()
m = re.search(r'^version\s*=\s*[\"\']?([0-9]+\.[0-9]+\.[0-9]+)', text, re.MULTILINE)
print(m.group(1) if m else 'UNKNOWN')
")
  echo "SKILL.md=${SRC_VER} · dist=${PKG_VER} · pyproject=${PYPROJ_VER}"
  if [[ "${SRC_VER}" != "${PKG_VER}" || "${SRC_VER}" != "${PYPROJ_VER}" || "${SRC_VER}" == "UNKNOWN" ]]; then
    echo "❌ 版本不一致（SKILL.md / dist 包 / pyproject 三方未对齐）——禁止宣称已分发"
    exit 1
  fi
  # git tag 核对（非 git 仓库/无 tag 时降级为警告，不阻断）
  if git -C "${ROOT}" describe --tags --abbrev=0 >/dev/null 2>&1; then
    TAG_VER=$(git -C "${ROOT}" describe --tags --abbrev=0 | sed 's/^v//')
    if [[ "${TAG_VER}" != "${SRC_VER}" ]]; then
      echo "⚠️ git tag(v${TAG_VER}) 与包版本(${SRC_VER}) 不一致——发布前需补打 tag"
    else
      echo "✅ git tag v${TAG_VER} 与包版本一致"
    fi
  else
    echo "ℹ️ 非 git 仓库或无 tag，跳过 git tag 核对"
  fi
fi

# 前置断言：安装目录必须存在且非空、ROOT != INSTALL_DIR（2026-08-05 三轮审查 R-1 修复：
# 原实现安装目录缺失时 diff 报错被 2>/dev/null 吞掉 → 误判「零差异」假阳性）
assert_install_dir() {
  if [[ ! -d "${INSTALL_DIR}" ]]; then
    echo "❌ 安装目录不存在：${INSTALL_DIR}（无法复验，禁止宣称零差异）"
    exit 1
  fi
  if [[ "$(find "${INSTALL_DIR}" -mindepth 1 -type f 2>/dev/null | wc -l)" -eq 0 ]]; then
    echo "❌ 安装目录为空：${INSTALL_DIR}（无文件可复验）"
    exit 1
  fi
  if [[ "${ROOT}" == "${INSTALL_DIR}" ]]; then
    echo "❌ ROOT == INSTALL_DIR（自比较恒为零差异，禁止宣称分发一致性）"
    exit 1
  fi
}

# --skip-package 模式（2026-08-05 实证核查修复：安装版目录无 dist/，直接做 diff 复验，
# 不再强制要求 .skill 存在——解决「门禁只能在开发仓库全过」的目录悖论）
if [[ "${SKIP_PACKAGE}" == "--skip-package" ]]; then
  echo ""
  echo "[复验] 安装版 vs 源码版一致性（--skip-package 模式，跳过打包/安装）..."
  assert_install_dir
  DIFFS=$(diff -rq "${INSTALL_DIR}" "${ROOT}" \
    --exclude="__pycache__" --exclude=".pytest_cache" --exclude=".ruff_cache" \
    --exclude="dist" --exclude=".git" --exclude="*.pyc" \
    --exclude="s7-final-check.md" \
    --exclude=".rufftmp" --exclude="*.log" --exclude=".vf_tmp.log" --exclude="tests" --exclude="docs" 2>/dev/null | grep -E "^Files|^Only" | wc -l) || true
  if [[ "${DIFFS}" -eq 0 ]]; then
    echo "✅ 安装版 = 源码版（零差异）"
    echo ""
    echo "=== O-5 校验通过 ==="
    exit 0
  else
    echo "❌ 检测到 ${DIFFS} 个文件差异（安装漂移！）"
    diff -rq "${INSTALL_DIR}" "${ROOT}" \
      --exclude="__pycache__" --exclude=".pytest_cache" --exclude=".ruff_cache" \
      --exclude="dist" --exclude=".git" --exclude="*.pyc" \
      --exclude="s7-final-check.md" \
      --exclude=".rufftmp" --exclude="*.log" --exclude=".vf_tmp.log" --exclude="tests" --exclude="docs" 2>/dev/null | grep -E "^Files|^Only" | head -20 || true
    echo ""
    echo "=== O-5 校验失败：禁止宣称已分发，请重新打包安装 ==="
    exit 1
  fi
fi

# 完整流程入口（打包+版本核对之后、安装之前）：防 INSTALL_DIR==ROOT 自清空（R38；temp 模式目录尚不存在，只比对路径）
if [[ "${ROOT}" == "${INSTALL_DIR}" ]]; then
  echo "❌ ROOT == INSTALL_DIR（自比较恒为零差异，禁止宣称分发一致性）"
  exit 1
fi

# 2) 安装（覆盖式解压）
echo ""
echo "[3/4] 覆盖安装到 ${INSTALL_DIR} ..."
SKILL_ZIP="${REPO_ROOT}/dist/devorder-guide.skill"
if [[ ! -f "${SKILL_ZIP}" ]]; then
  echo "❌ .skill 不存在：${SKILL_ZIP}"
  exit 1
fi
mkdir -p "${INSTALL_DIR}"
# 清空目标目录，防旧包残留（.ruff_cache 等非排除项历史残留）——2026-08-05 O-1' 修复
find "${INSTALL_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
(cd "${INSTALL_DIR}" && PYTHONUTF8=1 "${PYTHON}" -c "
import sys, zipfile, os
from pathlib import Path
z = zipfile.ZipFile(r'${SKILL_ZIP_WIN}')
for name in z.namelist():
    # v0.5.26 Zip Slip 防护（P-02）：拒绝 '..' 路径段与绝对路径，防止解压逃逸目标目录
    parts = Path(name).parts
    if any(p == '..' for p in parts) or os.path.isabs(name):
        print(f'❌ Zip Slip 拦截：条目 {name!r} 含非法路径'); sys.exit(1)
    target = Path(name)
    if name.endswith('/'):
        target.mkdir(parents=True, exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(name))
print('✅ 解压完成（含 Zip Slip 防护）')
")

# 3) 一致性复验（排除运行时产物；scripts/ 在包内已纳入复验，2026-08-05 复审 N6 注释同步）
echo ""
echo "[4/4] 安装版 vs 源码版一致性复验 ..."
DIFFS=$(diff -rq "${INSTALL_DIR}" "${ROOT}" \
  --exclude="__pycache__" --exclude=".pytest_cache" --exclude=".ruff_cache" \
  --exclude="dist" --exclude=".git" --exclude="*.pyc" \
  --exclude="s7-final-check.md" \
  --exclude=".rufftmp" --exclude="*.log" --exclude=".vf_tmp.log" --exclude="tests" --exclude="docs" 2>/dev/null | grep -E "^Files|^Only" | wc -l) || true
if [[ "${DIFFS}" -eq 0 ]]; then
  echo "✅ 安装版 = 源码版（零差异）"
  echo ""
  echo "=== O-5 校验通过 ==="
  exit 0
else
  echo "❌ 检测到 ${DIFFS} 个文件差异（安装漂移！）"
  diff -rq "${INSTALL_DIR}" "${ROOT}" \
    --exclude="__pycache__" --exclude=".pytest_cache" --exclude=".ruff_cache" \
    --exclude="dist" --exclude=".git" --exclude="*.pyc" \
    --exclude="s7-final-check.md" \
    --exclude=".rufftmp" --exclude="*.log" --exclude=".vf_tmp.log" --exclude="tests" --exclude="docs" 2>/dev/null | grep -E "^Files|^Only" | head -20 || true
  echo ""
  echo "=== O-5 校验失败：禁止宣称已分发，请重新打包安装 ==="
  exit 1
fi
