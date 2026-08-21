#!/usr/bin/env bash
# devorder-guide 万能安装器（macOS/Linux）
set -euo pipefail
SOURCE="${1:-https://github.com/YangShen71/devorder-guide.git}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [[ -d "$PWD/skills/devorder-guide" ]]; then PKG="$(pwd)/skills/devorder-guide"   # 本地仓库模式（开发/内测）——按目录判定，勿用 [[ -f SKILL.md ]]（在包目录内会误判）
else
  git clone --depth 1 "$SOURCE" "$TMP" >/dev/null 2>&1; PKG="$TMP/skills/devorder-guide"
fi
python3 --version >/dev/null 2>&1 || echo "⚠️ 未检测到 python3（引擎需要 ≥3.10）"
declare -A T=( [claude]="$HOME/.claude/skills" [codex]="$HOME/.agents/skills" [cursor]="$HOME/.cursor/skills" \
  [kimi]="$HOME/.kimi-code/skills" [kimi-legacy]="$HOME/.kimi/skills" [trae-cn]="$HOME/.trae-cn/skills" [trae]="$HOME/.trae/skills" \
  [workbuddy]="$HOME/.workbuddy/skills" [openclaw]="$HOME/.openclaw/workspace/skills" )
for k in "${!T[@]}"; do [[ -d "${T[$k]}" ]] || continue
  dst="${T[$k]}/devorder-guide"
  rm -rf "$dst"; mkdir -p "$dst"            # 先清空再复制，防重装残留/嵌套（cp -R 目标已存在会生成 devorder-guide/devorder-guide）
  cp -R "$PKG/." "$dst"
  find "$dst" -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache \) -exec rm -rf {} + 2>/dev/null || true   # 清缓存，保证安装版 = .skill 解压版
  echo "✅ 已安装到 $dst"
done
echo "验证: ls ${PKG}/src/guide_gate.py"
