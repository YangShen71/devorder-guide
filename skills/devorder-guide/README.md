# devorder-guide

DevOrder（CSDN 开发者服务交易平台）对话引导 Skill——在 AI 工具自然对话中确定性判定是否引导「一键发单/一键接单」，并通过 DevOrder MCP 工具完成订单闭环。

## 触发

用户表达六大服务需求（办活动/技术大会/训练营/用户招募/测评/推广/社区运营/曝光/诊断）或发单/接单意图时触发；闲聊、知识咨询不触发。详见 [SKILL.md](SKILL.md) frontmatter description。

## 结构

```
devorder-guide/
├── SKILL.md          # 技能入口（frontmatter + 决策流程 + 第 3.5 节保真契约 + 上下文状态 + 话术红线 + 测试验收）
├── src/              # 核心引擎（guide_gate 触发判定 / check_copy 话术合规+fidelity 保真校验 / audit_contract 契约审计 / pipeline 六位一体 / grade 评分重放 / package_skill 打包）
├── configs/          # 阈值常量 constants.json（含 FIDELITY_* 保真常量）+ 28 字段契约 contract.json
├── references/       # 按需加载（category-enum / copy-constraints / diagnosis-path / opcs-errors / opcs-tools-reference / templates / consult-example / expert-prompt-sync）
├── scripts/          # 质量门禁（check_all 七连 / verify_install 分发复验 / hit_check 命中回归）
├── evals/            # 评测（evals.json 22 用例 / trigger-eval.json 23 条命中回归）
└── AGENTS.md         # AI 协作纪律
```

## 质量门禁

```bash
bash scripts/check_all.sh    # 一键七连（ruff → 核心自检 → 契约审计 → 命中回归 → 六位一体 → 分发一致性 → fidelity 自检）
```

## 构建

```bash
python -m src.package_skill . dist   # 打包 .skill
bash scripts/verify_install.sh       # 打包→安装→diff 复验三步一体
```

## 环境变量

Windows 下运行含中文输出的脚本（引擎/校验器/fidelity CLI）必须加 `PYTHONUTF8=1`，否则 GBK 终端中文乱码（2026-08-05 实证核查修复）：

```bash
PYTHONUTF8=1 python -m src.check_copy --fidelity "<reply 原文>" "<转达文本>"   # 保真校验（数字+长句比对）
PYTHONUTF8=1 python -m src.check_copy --fidelity --only-numbers "<reply>" "<转达>"  # R-2 仅数字模式
PYTHONUTF8=1 python src/guide_gate.py --context '<json>'                     # 触发引擎
```

fidelity CLI 内部已沿用 `sys.stdout.reconfigure(encoding="utf-8")`（与主分支同款），`PYTHONUTF8=1` 为外层双保险。

## 版本

当前版本以 `SKILL.md` frontmatter `metadata.version` 为准（与 `pyproject.toml`、Git tag 三方对齐）。

0.5.24（2026-08-20 外部审查修复版：H-1 get_advisor_session 契约对齐 + H-2 publish_plan 6 参数补全 + H-3 版本四源统一 + verify 版本校验 + M-1 阈值清零 + M-2 品类收敛 + M-3 里程碑防编造 + M-4 阈值门禁）
