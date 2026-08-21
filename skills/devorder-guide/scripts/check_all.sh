#!/usr/bin/env bash
# check_all.sh — 一键七连质量检查（O-1' 深度优化）
#
# 用途：devorder-guide 全量质量门禁，一条命令跑完六项检查。
# 用法：bash scripts/check_all.sh
# 退出码：0 = 全部通过；非 0 = 存在失败项
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"   # scripts/../../.. = 仓库根（dist 产物在仓库根；第七轮修正层级）
# 2026-08-12 修复：PYTHON 默认指向 managed default venv（含 pytest），
# 避免裸 python 解析到无 pytest 的解释器导致六位一体 TESTS 误败
PYTHON="${PYTHON:-$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe}"
RUFF="${RUFF:-$HOME/.workbuddy/binaries/python/envs/default/Scripts/ruff.exe}"

# Windows 下 venv 不存在时回退 PATH（-x 不查 PATH：裸命令名须 command -v 兜底，否则 PYTHON=python3 会被误覆写）
if [[ ! -x "${PYTHON}" ]] && ! command -v "${PYTHON}" >/dev/null 2>&1; then
  PYTHON="python"
fi

# Windows 下 ruff 不在 PATH 时用 venv 绝对路径（同上：裸命令名须 command -v 兜底）
if [[ ! -x "${RUFF}" ]] && ! command -v "${RUFF}" >/dev/null 2>&1; then
  RUFF="ruff"
fi

cd "${ROOT}"
FAILED=0

echo "============================================"
echo "DevOrder 质量检查（七连）"
echo "============================================"

check() {
  local name="$1"; shift
  echo ""
  echo "── [$name] ──"
  "$@" || { echo "❌ [$name] 失败"; FAILED=1; }
}

# 1. ruff lint（精简版仅 src/，tests/ 在开发仓库）
check "ruff check" "${RUFF}" check src/ --no-cache
# 2. ruff format
check "ruff format" "${RUFF}" format --check src/
# 3. 核心功能自检（12 场景；开发仓库另有完整 pytest 集）
check "核心自检" env PYTHONUTF8=1 "${PYTHON}" -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('gg', 'src/guide_gate.py')
gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
base = {'sessionId':'t','platform':'workbuddy','platformCompatible':True,'userIntent':'issue_order','category':'event','confidence':0.8,'slotFill':0.6,'round':5,'guideCountThisHour':0,'lastSameCategoryMinutesAgo':30,'rejectionFlags':{},'postRejectionWeakShown':{},'activeOrders':[],'userRole':'issuer','guideHistory':[],'painKeywords':False,'goalKeywords':True,'specType':'dedicated','matchedOrderCount':0,'orderQuality':None,'hasNewDemandSignal':False,'subtype':'competition','phase':'gather'}
cases = [
  (dict(base), True), (dict(base, category='user_acquisition', phase='ready', slotFill=1.0, round=8, confidence=0.9), True),
  (dict(base, userIntent='pick_order', userRole='picker', round=3, matchedOrderCount=2, orderQuality='partial', phase='gather'), True),
  (dict(base, userIntent='consult'), False), (dict(base, guideCountThisHour=5), False),
  (dict(base, rejectionFlags={'event':True}, hasNewDemandSignal=True), True),
  (dict(base, userIntent='chitchat'), False), (dict(base, opcsCallsLastMinute=100), False),
  (dict(base, specType='dedicated', slotFill=0.2, round=6), True),
  # 2026-08-05 三轮审查 A-1：接单 phase 闸（proposal/idle 静默）
  (dict(base, userIntent='pick_order', userRole='picker', matchedOrderCount=2, phase='proposal'), False),
  (dict(base, userIntent='pick_order', userRole='picker', matchedOrderCount=2, phase='idle'), False),
  # 2026-08-05 三轮审查 A-2：接单拒绝+新信号 → weak 无入口
  (dict(base, userIntent='pick_order', userRole='picker', matchedOrderCount=2, phase='gather', rejectionFlags={'order_pick':True}, hasNewDemandSignal=True), True),
]
for i, (ctx, exp) in enumerate(cases):
    got = gg.guide_gate(ctx)['trigger']
    if got != exp:
        print(f'❌ 场景{i+1} 期望{exp} 实际{got}'); sys.exit(1)
# 场景 12 额外断言：接单拒绝降级为 weak 且无入口
o12 = gg.guide_gate(cases[11][0])
if o12.get('intensity') != 'weak' or o12.get('tool') is not None:
    print(f'❌ 场景12 拒绝降级 期望 weak+null 实际 {o12.get("intensity")}/{o12.get("tool")}'); sys.exit(1)
print('✅ 12 场景核心自检通过')
"
# 4. 契约审计
check "契约审计" env PYTHONUTF8=1 "${PYTHON}" -m src.audit_contract src/guide_gate.py
# 4.5 命中回归（2026-08-05 三轮审查 F-2：AGENTS 声称六连含 hit_check 但此前未调用）
check "命中回归" env PYTHONUTF8=1 "${PYTHON}" scripts/hit_check.py
# 5. 六位一体
check "六位一体" env PYTHONUTF8=1 "${PYTHON}" -m src.pipeline
# 6. 分发一致性（打包→安装→diff 复验）
check "分发一致性" bash scripts/verify_install.sh --temp-install

# 7. fidelity 自检回归（2026-08-18 P1-5 T-1：每次跑 check_all 自动验证 fidelity_check 可用）
# ⚠️ 修正方案原文断言（v1.1 缺陷）：G7 灰度默认 warn，缺失样例 exit=0 属正常；
#    故按 JSON 输出 passed 字段判定（完整=passed:true / 缺失=passed:false），与模式无关
if [[ -x "${PYTHON}" ]] || command -v "${PYTHON}" >/dev/null 2>&1; then   # -x 不查 PATH：裸命令名（CI 的 PYTHON=python）须 command -v 兜底，否则 fidelity 段静默跳过
  echo ""
  echo "── [FIDELITY 自检] ──"
  if "${PYTHON}" -m src.check_copy --fidelity "目标 2000 人" "目标 2000 人" 2>/dev/null | grep -q '"passed": true'; then
    echo "[✅ PASS] FIDELITY 完整返回（passed=true）"
  else
    echo "[❌ FAIL] FIDELITY 完整返回校验失败"
    FAILED=1
  fi
  if "${PYTHON}" -m src.check_copy --fidelity "目标 2000 人预算 60 万" "目标 2000 人" 2>/dev/null | grep -q '"passed": false'; then
    echo "[✅ PASS] FIDELITY 缺失检出（passed=false，missing 含目标数字）"
  else
    echo "[❌ FAIL] FIDELITY 缺失检测失败（应检出 passed=false）"
    FAILED=1
  fi
fi

echo ""
echo "============================================"
if [[ "${FAILED}" -eq 0 ]]; then
  echo "✅ 七连全部通过"
  echo ""
  echo "── 实测数字（发布声明用，2026-08-05 复审 N7 纪律）──"
  echo "  引擎行数: $(wc -l < src/guide_gate.py) | contract 字段: $(PYTHONUTF8=1 "${PYTHON}" -c "import json;print(len(json.load(open('configs/contract.json',encoding='utf-8'))['fields']))" 2>/dev/null || echo '?')"
  echo "  审计: $(PYTHONUTF8=1 "${PYTHON}" -m src.audit_contract src/guide_gate.py 2>/dev/null | grep -oE '(总数|trigger 返回): [0-9]+' | tr '\n' ' ')"
  echo "  dist 包: $(PYTHONUTF8=1 "${PYTHON}" -c "import zipfile;print(len(zipfile.ZipFile(r'$(cygpath -w "${REPO_ROOT}/dist/devorder-guide.skill" 2>/dev/null || echo "${REPO_ROOT}/dist/devorder-guide.skill")').namelist()),'文件')" 2>/dev/null || echo '?') / $(du -h "${REPO_ROOT}/dist/devorder-guide.skill" 2>/dev/null | cut -f1)"
  exit 0
else
  echo "❌ 存在失败项（见上）"
  exit 1
fi
