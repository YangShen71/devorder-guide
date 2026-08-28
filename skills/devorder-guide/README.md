# devorder-guide

DevOrder（CSDN 开发者服务交易平台）对话引导 Skill——在 AI 工具自然对话中确定性判定是否触发「一键发单/一键接单」，并通过 DevOrder MCP 工具完成订单闭环。

## 触发

用户表达六大服务需求（办活动/技术大会/训练营/用户招募/测评/推广/社区运营/曝光/诊断）或发单/接单意图时触发；闲聊、知识咨询不触发。详见 [SKILL.md](SKILL.md) frontmatter description。

## 结构

```
devorder-guide/
├── SKILL.md          # 技能入口（frontmatter + 第 0 步版本检查 + 决策流程 + 第 4.5 节保真契约 + 上下文状态 + 话术红线 + 测试验收）
├── src/              # 核心引擎（guide_gate 触发判定 / check_copy 话术合规+fidelity 保真校验 / audit_contract 契约审计 / pipeline 六位一体 / grade 评分重放 / package_skill 打包）
├── configs/          # 阈值常量 constants.json（含 FIDELITY_* 保真常量）+ 28 字段契约 contract.json
├── references/       # 按需加载（category-enum / copy-constraints / diagnosis-path / opcs-errors / opcs-tools-reference / templates / consult-example / expert-prompt-sync）
├── scripts/          # 质量门禁（check_all 七连 / verify_install 分发复验 / hit_check 命中回归 / update.py 版本检查与自更新）
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

当前版本以 `SKILL.md` frontmatter `version` 字段为准（与 `pyproject.toml`、运营端上传表单三方对齐）。版本号采用三段式语义化版本（`主版本.次版本.修订版本`），符合 `skill-package-generation-guide.md` 约定。

- `1.4.7`：更新改为删除替代（2026-08-26，PATCH）。用户明确要求「旧版本删除替代、不留备份」——更新成功后旧版被删除（替代而非备份），并清理历史遗留 `.bak`/`.old` 目录，文件系统只剩唯一主目录，从物理上根除宿主误识别备份目录的问题。改动：SKILL.md 第 0 步脚本 + update.py do_update 改为「move 到临时废弃位 → 新包就位 → 删除旧版 + 清理历史目录」；失败仍自动回滚；update.py --rollback 兼容 `.bak`/`.old` 两前缀。引擎零改动。
- `1.4.6`：边界与一致性修复（2026-08-26，PATCH）。全面严格检查发现 3 项并修复：①【P2】DIR_IS_BACKUP 时自动更新会写错位置（宿主从备份目录加载时 SKILL_DIR 指向 .bak，若继续自动更新会把备份目录当主目录覆盖、加剧错乱——已改为跳过自动更新）；②【P3】扁平包 move 临时目录边界 bug（pkg 即临时目录本身时 move 会导致清理报错——加 pkg==d 判断，扁平包用 copytree）；③【P2】references 模型名规则强度不一致（"默认隐藏" vs 主文件"必须隐藏"——对齐为"必须隐藏"）。引擎零改动。
- `1.4.5`：回滚失效回归修复 + 原子替换（2026-08-26，PATCH）。严格排查 v1.4.4 改动发现 4 个 Bug 并修复：①【P1】update.py `--rollback` 回滚功能失效（do_update 备份已移到 skill-backups/，但 do_rollback 仍只在 skills 目录 glob——已改扫两处）；②【P2】平台线脚本非原子替换（逐文件 copytree/copy2 → 改 move 原子替换）；③【P2】平台线脚本不删残留文件（move 后旧目录整体清空，无残留）；④【P3】SKILL.md 文档滞后（"旧版保留于 .bak-*" → "skill-backups/"）。引擎零改动。
- `1.4.4`：备份目录治理（2026-08-26，PATCH）。深度排查发现「宿主加载备份目录而非主目录」的版本管理问题——根因四层叠加（L1 无激活标记/L2 无更新通知/L3 .bak 命名同构/L4 脚本占位符语义 bug）。修复：SKILL.md 第 0 步自动更新脚本备份路径从 `~/.workbuddy/skills/devorder-guide.bak-{ver}` 改为 `~/.workbuddy/skill-backups/`（物理脱离宿主扫描范围，根治 L3）；新增「目录健康自检」前置步骤（主动暴露宿主从备份目录加载的失同步问题）；update.py 备份路径同步改造。引擎零改动。
- `1.4.3`：输出硬约束与「引导」两字清零 + 映射表自洽（2026-08-25，PATCH）。用户实测发现 4 类问题反复违规——(1) trigger=false 时输出"判定依据"调试表格暴露内部字段（2）转话阶段缺 5 段能量条（3）显示模型名（4）「强引导」「触发引导」等仍出现。严格根因：v0.5.29 净化仅覆盖 SKILL.md 主文件，references/ 残留 40 处"引导"；弱约束未配反例+处置。修复：SKILL.md 新增「输出硬约束（红线）」段（4 条硬禁令 + 违规处置 + 替换映射表），L229/L442 弱约束改硬禁止；references/ 全扫替换（copy-constraints 13 / consult-example 4 / category-enum 1 / opcs-errors 19 / opcs-tools-reference 3）；红线 2 映射表 L191/L192 重叠歧义修正。引擎零改动。
- `1.4.2`：测试版本（2026-08-25）。纯 PATCH 版本号升级，内容同 v1.4.1（用于实测第 0 步版本检查与自动更新链路）。引擎零改动。
- `1.4.1`：文案修正与歧义治理（2026-08-24）。全面严格验收 6 项修复：pytest 声明对齐实测（59→65，红线⑤实测背书）；forceUpdate 语义澄清（消除与「下次会话生效」的互斥表述——先完成替换→尝试重读新版→无法重载则告知重启，不阻断）；模型名规则跨文件对齐主文件「默认隐藏模型」；AGENTS.md 清除不存在文件（timing.json）引用；SKILL.md 4 处日期状态标注净化（读起来像一次写成的定稿）。引擎零改动。
- `1.4.0`：版本检查升为「第 0 步」（2026-08-24）。针对深度研究报告「版本检查被 AI 当背景信息略读而漏检（5/5 步全跳过）」：版本检查从元数据章节说明提升为「第 0 步：执行前版本检查（⚠️ 第一个动作 · 无例外）」——动作清单化 + 跳过后果警示；决策流程步骤整体后置（意图预分类/确定性引擎/生成话术/衔接执行/返回转达/对话恢复 → 第 1~5 步 + 第 4.5 步）；自动更新脚本健壮化（兼容平台包外层目录结构、Zip Slip 防护、SKILL_DIR 显式定位、顶层 version 行校验——沙盒演练 9/9 PASS）；新增「编号区分」注释消除服务端顾问进度与决策流程两种步骤编号的歧义。引擎零改动。
- `1.3.2`：测试版本（2026-08-24）。纯 PATCH 版本号升级，内容同 v1.3.1。引擎零改动。
- `1.3.0`：新增每次执行前自动版本检查（2026-08-24）。SKILL.md「版本检查与自动更新」章节新增「AI 模型必读·主路径」段（读 frontmatter → curl 接口 → 比对 latestVersion → 一致静默继续 / 不一致自动下载校验替换重载 → fail-closed 不阻断；24h 节流）；现有 Harness 自动层 + 开源线 `update.py` 兜底段整合为「三层检查架构」。补 description 未动（防 hit_check 漂移）。引擎零改动。
- `1.2.7`：闭环修正（2026-08-24）。平台规则「同身份+同版本不允许重复上传」→ 升 PATCH 版补回 v1.2.6 README 版本条目（追溯性）+ tag 链延长（→ v1.2.6）。补齐「平台包=源码零差异」一致性；引擎零改动。
- `1.2.6`：平台版本对齐（2026-08-24）。上传版本号对齐运营端（> 平台当前 1.2.4），包内 version=1.2.6 与表单一致（约定 §3 三处一致）；引擎零改动。
- `1.2.3`：二轮深度审查（2026-08-24）。全包清除 9 处 v1.x/v2.x/v3.x/v4.0/v5.0 历史版本标注残留（SKILL.md/category-enum/opcs-errors/templates/consult-example/copy-constraints/contract.json）；update.py UA 版本号同步；引擎零改动。
- `1.2.2`：明确更新渠道层级（2026-08-24）。主渠道 = 平台线 Harness 自动更新（`devorder.csdn.net` 服务端返回的 downloadUrl，生产环境稳定渠道）；兜底渠道 = 开源线 update.py（仅主渠道不可达时使用）。
- `1.2.1`：版本标注净化（2026-08-24）。全包清除 50+ 处 v0.x 历史版本标注（SKILL.md/references/configs），文件读起来像一次写成的定稿；修复「正确工作流」编号错位（3→4/5/6）与「strong strong」文字重复；引擎零改动。
- `1.2.0`：双形态打包 + schema 不固化整改（2026-08-24）。package_skill.py 新增 `--platform-pack` 产出外层目录形态 `-upload.zip`（约定 §1：SKILL.md 位于压缩包根目录的 Skill 目录中，供平台上架）；opcs-tools-reference.md 删除完整参数签名表（约定 §1：不固化工具 schema，参数以 MCP 返回为准）。
- `1.1.0`：新增 update.py 全平台版本检查/自更新器（2026-08-24）。SKILL.md 版本检查章节扩展为双段（平台线 Harness 约定接口 + 开源线 update.py 一句话触发）；接单路径声明弃用（迁移至独立 CONTRACTOR 技能，行为零改动）；新增 test_update.py 单测 6 用例。引擎零改动。
- `1.0.0`：首次按 Skill 包版本更新约定发布（2026-08-24）。frontmatter 新增 `identity: CUSTOMER` + `version` 提升顶层 + 新增「版本检查与自动更新」章节。引擎零改动。
- `0.5.x`：内部开发版本（未上传运营端），Git tag 链 v0.5.20 → v0.5.29 → v1.0.0 → v1.1.0 → v1.2.0 → v1.2.1 → v1.2.2 → v1.2.3 → v1.2.4 → v1.2.6 → v1.2.7 → v1.3.0 → v1.3.1 → v1.3.2 → v1.4.0 → v1.4.1 → v1.4.2 → v1.4.3 → v1.4.4 → v1.4.5 → v1.4.6 → v1.4.7 完整可回退。

## 更新方式

**三层检查架构**（互补双保险 + 兜底，详见 SKILL.md「第 0 步：执行前版本检查」段）：

| 层级 | 触发方 | 时机 | 适用 |
|---|---|---|---|
| **L1 AI 模型自动检查**（主路径） | AI 模型读 SKILL.md 指令 | 每次执行本 Skill 前（24h 节流） | WorkBuddy 等无 Harness 集成宿主 |
| **L2 平台线 Harness 自动更新** | 宿主 Harness | Harness 启动时/按更新策略 | 已集成 DevOrder Harness 的宿主 |
| **L3 开源线 `update.py` 兜底** | 用户触发或脚本 | 主动执行 `--check/--yes` | 离线/主渠道+模型自动均失效时 |

**L1 模型自动检查（第 0 步主路径）**：AI 模型加载本 Skill 后**第一个动作**——读 `SKILL.md` frontmatter 当前 `version` → 用 python3 urllib 内联脚本调 `GET ...?identity=CUSTOMER&currentVersion={ver}` → 比对 `latestVersion` → 一致静默继续 / 不一致走自动更新流程（下载→校验→备份→替换）。跳过检查 = 流程违规（有跳过后果警示）。fail-closed 不阻断用户。

**L2 主渠道（默认）**：平台线 Harness 自动更新 —— Harness 启动时或按更新策略调用 `GET /api/v1/skills/version?identity=CUSTOMER&currentVersion={ver}`，读取响应中的 `latestVersion` 和 `downloadUrl` 自动下载校验替换（生产环境稳定渠道，地址由 `devorder.csdn.net` 服务端返回）。

**L3 兜底渠道（仅主渠道 + 模型自动均失效时使用）**：开源线 `update.py`（GitHub/GitCode 源），用于无平台线集成 + 模型自动失败的极端场景：

| 工具 | 兜底更新方式 | 档位 |
|---|---|---|
| Claude Code | 开启 autoUpdate 后完全自动（/plugin → Marketplaces → devorder-guide → Enable auto-update） | T1 全自动 |
| Codex / Cursor / 其他 CLI | `gh skill update devorder-guide`（GitHub CLI ≥ 2.90） | T2 半自动 |
| WorkBuddy | 对 AI 说「检查 devorder-guide 更新」→ 技能自带 `update.py` 完成检查/更新 | T2 半自动 |
| InsCode | 下载最新 Release 的 `devorder-guide.skill` 手动重导 | T3 手动 |

> 主渠道 = 平台线 Harness 自动更新（默认，地址由 `devorder.csdn.net` 服务端返回）；兜底渠道 = 开源线 `update.py`（仅主渠道 + 模型自动均失效时使用）。两渠道版本号各自独立、不混比。
