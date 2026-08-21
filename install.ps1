# devorder-guide 万能安装器（Windows）
# 用法:  powershell -ExecutionPolicy Bypass -File install.ps1 [-Source <git-url>] [-Tools auto|claude,codex,...] [-DryRun]
param(
    [string]$Source = "https://github.com/<owner>/devorder-guide.git",
    [string]$Tools = "auto",
    [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$tmp = Join-Path $env:TEMP ("devorder-guide-" + [guid]::NewGuid().ToString("N"))

# 1) 获取源码
Write-Host "[1/4] 拉取仓库: $Source" -ForegroundColor Cyan
if (Test-Path (Join-Path $PWD "skills\devorder-guide\SKILL.md")) {
    $pkg = Join-Path $PWD "skills\devorder-guide"   # 本地仓库模式（开发/内测）——按产物存在判定，勿用 .git（客户在自己 git 项目里运行会误判）
    Write-Host "      使用本地仓库" -ForegroundColor DarkGray
} else {
    git clone --depth 1 $Source $tmp | Out-Null
    $pkg = Join-Path $tmp "skills\devorder-guide"
}
if (-not (Test-Path (Join-Path $pkg "SKILL.md"))) { throw "源码中未找到 SKILL.md: $pkg" }

# 2) Python 检查（引擎必需）
Write-Host "[2/4] 检查 Python 3.10+" -ForegroundColor Cyan
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if ($py) {
    $ver = & $py.Source --version 2>&1
    Write-Host "      检测到: $ver" -ForegroundColor DarkGray
} else {
    Write-Warning "未检测到 Python。引擎运行需要 Python 3.10+（python.org 或 winget install Python.Python.3.12）。"
    Write-Host "      可先安装后重跑本脚本，或由 AI 工具代为安装。" -ForegroundColor Yellow
}

# 3) 工具检测与安装
Write-Host "[3/4] 检测并安装到已存在的工具目录" -ForegroundColor Cyan
$targets = @{
    "claude"    = "$HOME\.claude\skills"
    "codex"     = "$HOME\.agents\skills"
    "cursor"    = "$HOME\.cursor\skills"
    "kimi"      = "$HOME\.kimi-code\skills"
    "kimi-legacy" = "$HOME\.kimi\skills"
    "trae-cn"   = "$HOME\.trae-cn\skills"
    "trae"      = "$HOME\.trae\skills"
    "workbuddy" = "$HOME\.workbuddy\skills"
    "openclaw"  = "$HOME\.openclaw\workspace\skills"
}
$installed = @()
$selected = @($targets.Keys | Sort-Object)
if ($Tools -ne "auto") { $selected = @($Tools -split "," | ForEach-Object { $_.Trim() }) }
foreach ($t in $selected) {
    $dir = $targets[$t]
    if (-not $dir) { Write-Warning "未知工具: $t"; continue }
    if (-not (Test-Path $dir)) {
        if ($Tools -ne "auto") { Write-Warning "目录不存在，跳过 $t : $dir" }
        continue
    }
    $dst = Join-Path $dir "devorder-guide"
    if ($DryRun) { Write-Host "      [dry] 将安装到 $dst" -ForegroundColor DarkGray; continue }
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }   # 清空旧版再复制，防残留文件（幂等）
    Copy-Item -Recurse -Force (Join-Path $pkg "*") $dst
    Get-ChildItem -Path $dst -Directory -Recurse -Force | Where-Object { $_.Name -in @("__pycache__", ".pytest_cache", ".ruff_cache") } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue   # 清缓存，保证安装版 = .skill 解压版
    $installed += "$t -> $dst"
}
Write-Host ("[4/4] 完成。" + $(if ($installed.Count) { " 已安装: " + ($installed -join "; ") } else { " 未检测到目标工具目录（可手动复制 $pkg 到对应技能目录）" })) -ForegroundColor Green
Write-Host "验证: 查看技能目录下应有 src\guide_gate.py 与 configs\constants.json"
if ($DryRun) { Write-Host "（--dry-run 预览模式，未实际安装）" -ForegroundColor DarkGray }
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }

