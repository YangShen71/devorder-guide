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

方案甲脚本（v1.5.5 · 单条调用，无需内联写代码）：

```bash
python scripts/run_gate.py --category event --subtype competition --confidence 0.9 \
  --slot-fill 0.6 --round 1 --goal-keywords 1 --spec-type dedicated --session-id do_xxx
python scripts/version_check.py   # 第 0 步版本检查（GO/UPDATE/SKIP 信号）
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

- `1.5.5`：输出作用域分离（2026-09-23，PATCH）。`check_copy` 首参收敛为「仅引导话术片段」——**业务内容**（顾问核心回复、需求梳理、品类范围说明、追问、结论）**不再参与** 80 字 / 退路 / 绝对化词校验（此前从文本开头截取计数，业务回复超 80 字即被误判并触发回退替换）；新增骨架业务占位符守卫（`[核心回复]` / `[顾问核心回复]` 未替换即判违规）；回退规则改为「**只回退话术部分，业务内容原样保留**」；`audit_contract` 新增 AST 断言（`check_copy` 首形参名须为 `guide`）；文档 12 处「80 字」表述统一加限定词并修正归类；单测 95 → **100**。引擎基线 `check_copy 89047fb3e370 → ` 变更（`guide_gate` / `contract` 未变）。
- `1.5.4`：引擎健壮性修复（2026-09-22，PATCH）。代码审查 7 项：`check_platform` 改严格布尔（此前 `'false'`/`1` 等 truthy 值可绕过平台兼容闸）；新增 `_num`/`_dict`/`_list` 类型安全读取，消除 **24 项类型注入崩溃**；`_round_score` 类型守卫；CLI `--confidence`/`--slot-fill` 补 0~1 范围校验；`--active-orders` 补非负校验；`check_frequency_cap` reason 去除引擎未实现的「静默 30 分钟」表述；`rejection_branch` 移除无消费方的冗余 `text` 键；`OPCS_ROLE_TOOLS` fallback 与 `constants.json` 逐项对齐。引擎基线 `guide_gate d69cd32152ee → 4b3e60d3ac0c`。
- `1.5.3`：内部执行说明泄漏修复（2026-09-22，PATCH）。会话实测事故驱动：输出中出现「执行说明（内部）」段（同时命中判定字段数值 / 英文品类枚举 / 工具调用叙述三类）→ 红线 3 补充真实事故原文示例，并说明 `check_copy` 门禁边界（其校验维度不含脱敏）。
- `1.5.2`：用户可见输出脱敏（2026-09-22，PATCH）。红线 3 作用域扩展为**全部用户可见输出**（含 `trigger=true` / 降级路径 / 转达 / 诊断路径，取消「只有 trigger=false 才禁」的误读），列明四类禁止内容 + 可删除性测试判据 + 白名单；`references/copy-constraints.md` 新增输出脱敏自检清单。
- `1.5.1`：速查表与映射精确化（2026-09-22，PATCH）。独立审查发现的文案级问题修正：① 速查表 `dev_growth` 行原列举「技术文章/白皮书」与 `content_writing` 触发词交叠 → 改为目标导向表述（「内容 + 分发到开发者聚集处」），`content_writing` 标注「纯交付，不含分发」；② `references/category-enum.md` 残留旧映射「海报/KV → exposure」→ 改为 `visual_design`；③ 手册映射表标题计数改为不依赖计数的表述。引擎三文件零改动（基线延续 v1.5.0）。
- `1.5.0`：品类枚举扩展（2026-09-22，MINOR）。新增 6 个需求品类（`software_build`/`content_writing`/`video_production`/`product_testing`/`visual_design`/`hardware_eng`，白名单 5→11），覆盖「造软件/写内容/出视频/做评测/做设计/造硬件」全部需求类型；`description` 重构（150 字符内，8 类需求 + 5 类不触发界定）；「第 2 步：运行确定性引擎」重写（4 步执行顺序 + 输出分派表 + 引擎 11 检查点 + 异常处理 + 降级条件修正）；触发词移除泛词「设计」并补 33 词（实测正例 45/45、反例 0/12）。**引擎白名单经书面授权变更**（红线基线已更新）。
- `1.4.36`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号递增，内容同 v1.4.35（用于实测自动更新闭环：本地 1.4.35 → 平台 1.4.36 → version_check UPDATE → update_apply 就地替换自动更新）。引擎三文件零改动（hash 硬闸）。
- `1.4.35`：就地替换修复（2026-09-14，PATCH）。真实事故驱动：三段式 move 在 Windows 上因进程 cwd 锁定 skill_dir 目录导致 os.rename 失败、shutil.move 静默回退 copytree+rmtree 把旧版清空（主目录只剩空 scripts、回滚失效）→ 改为「完整备份→就地清空→就地复制」+ 可靠回滚，全程不移动/删除 skill_dir 根目录；update_apply 内部 chdir 到系统临时目录 + skill_dir abspath 固化；新增 cwd 锁定回归 + 回滚失败两用例（单测 4→6）。引擎三文件零改动（hash 硬闸）。
- `1.4.34`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.33（连续闭环复测）。引擎三文件零改动（hash 硬闸）。
- `1.4.34`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.33（连续闭环复测）。引擎三文件零改动（hash 硬闸）。
- `1.4.33`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.32（连续闭环复测）。引擎三文件零改动（hash 硬闸）。
- `1.4.33`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.32（连续闭环复测）。引擎三文件零改动（hash 硬闸）。
- `1.4.32`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.31（用于实测三段式原子替换修复后的完整自动更新闭环）。引擎三文件零改动（hash 硬闸）。
- `1.4.32`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.31（用于实测三段式原子替换修复后的完整自动更新闭环）。引擎三文件零改动（hash 硬闸）。
- `1.4.31`：原子性缺口修复（2026-09-14，PATCH）。真实事故驱动：update_apply「move 旧版→copytree 新包」两步间进程中断导致主目录残缺（只剩空 scripts、回滚无法执行）→ **三段式原子替换**（新包先就位临时目录→move 旧版→单步 move 新目录；崩溃窗口缩至单步，任一时点可人工恢复）；失败路径补 staging 清理。引擎三文件零改动（hash 硬闸）。
- `1.4.31`：原子性缺口修复（2026-09-14，PATCH）。真实事故驱动：update_apply「move 旧版→copytree 新包」两步间进程中断导致主目录残缺（只剩空 scripts、回滚无法执行）→ **三段式原子替换**（新包先就位临时目录→move 旧版→单步 move 新目录；崩溃窗口缩至单步，任一时点可人工恢复）；失败路径补 staging 清理。引擎三文件零改动（hash 硬闸）。
- `1.4.30`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.29（用于实测「检测 UPDATE → 自动执行 update_apply」完整闭环）。引擎三文件零改动（hash 硬闸）。
- `1.4.30`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.29（用于实测「检测 UPDATE → 自动执行 update_apply」完整闭环）。引擎三文件零改动（hash 硬闸）。
- `1.4.29`：信号契约全覆盖（2026-09-14，PATCH）。① 脚本 20 信号 × 文档对账：补 NO_VERSION_FOUND/USAGE_ERROR 两行到 detail 结论表；② update_apply docstring 补 NETWORK_FAIL/INTERNAL_ERROR/UPDATE_TIMEOUT/USAGE_ERROR；③ 平台线失败兜底段 SHA256 残留澄清（SHA256 属开源线专用，平台线以版本校验为等价护栏）。引擎三文件零改动（hash 硬闸）。
- `1.4.29`：信号契约全覆盖（2026-09-14，PATCH）。① 脚本 20 信号 × 文档对账：补 NO_VERSION_FOUND/USAGE_ERROR 两行到 detail 结论表；② update_apply docstring 补 NETWORK_FAIL/INTERNAL_ERROR/UPDATE_TIMEOUT/USAGE_ERROR；③ 平台线失败兜底段 SHA256 残留澄清（SHA256 属开源线专用，平台线以版本校验为等价护栏）。引擎三文件零改动（hash 硬闸）。
- `1.4.28`：会话状态保护 + 双源漂移清零（2026-09-14，PATCH）。① update_apply 删除替代会连带删除用户 session.json（拒绝流/频率帽状态归零）→ 内存备份迁移修复；trash 时间戳微秒+pid 防并发撞名；② detail 残留 75 行旧 bash 更新段（用户手写脚本根源）→ 删除并改指 update_apply.py（唯一权威），detail 101→27 行；③ 测试用例 4 补 session 迁移断言。引擎三文件零改动（hash 硬闸）。
- `1.4.28`：会话状态保护 + 双源漂移清零（2026-09-14，PATCH）。① update_apply 删除替代会连带删除用户 session.json（拒绝流/频率帽状态归零）→ 内存备份迁移修复；trash 时间戳微秒+pid 防并发撞名；② detail 残留 75 行旧 bash 更新段（用户手写脚本根源）→ 删除并改指 update_apply.py（唯一权威），detail 101→27 行；③ 测试用例 4 补 session 迁移断言。引擎三文件零改动（hash 硬闸）。
- `1.4.27`：UPDATE 宿主交互面修复（2026-09-14，PATCH）。端到端实测暴露并修复：① 信号乱序（子进程 stdout 继承与父 print 缓冲乱序）→ capture_output 按序透传；② 更新失败 exit 1 违背 fail-closed → **return 0 不阻断**（旧版可用静默继续）+ UPDATE_TIMEOUT（120s）兜底；channels.md 失败兜底段补 update_apply 失败信号语义。引擎三文件零改动（hash 硬闸）。
- `1.4.27`：UPDATE 宿主交互面修复（2026-09-14，PATCH）。端到端实测暴露并修复：① 信号乱序（子进程 stdout 继承与父 print 缓冲乱序）→ capture_output 按序透传；② 更新失败 exit 1 违背 fail-closed → **return 0 不阻断**（旧版可用静默继续）+ UPDATE_TIMEOUT（120s）兜底；channels.md 失败兜底段补 update_apply 失败信号语义。引擎三文件零改动（hash 硬闸）。
- `1.4.26`：深度审查修复（2026-09-14，PATCH）。version_check docstring 移除已删除的 fresh 分支描述；update_apply 补 dl 完整 URL 防御；**新增 test_update_apply.py 4 用例**（USAGE_ERROR/VERSION_MISMATCH/ZIP_SLIP/成功路径——update_apply 零测试缺口关闭）。引擎三文件零改动（hash 硬闸）。
- `1.4.26`：深度审查修复（2026-09-14，PATCH）。version_check docstring 移除已删除的 fresh 分支描述；update_apply 补 dl 完整 URL 防御；**新增 test_update_apply.py 4 用例**（USAGE_ERROR/VERSION_MISMATCH/ZIP_SLIP/成功路径——update_apply 零测试缺口关闭）。引擎三文件零改动（hash 硬闸）。
- `1.4.25`：自动更新执行层固化（2026-09-14，MINOR）。方案 A：新增 scripts/update_apply.py（下载→校验→替换→收尾三件套，ZIP_SLIP 防护 + 版本校验 + 删除替代可回滚）；version_check.py 检测到 UPDATE 时自动调用（结束「检测与执行分离」缺口）；SKILL.md/channels/detail 同步「自动执行」表述。引擎三文件零改动（hash 硬闸）。
- `1.4.24`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.23（用于实测节流移除后的自动更新链路）。引擎三文件零改动（hash 硬闸）。
- `1.4.24`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.23（用于实测节流移除后的自动更新链路）。引擎三文件零改动（hash 硬闸）。
- `1.4.23`：模型检查层节流移除（2026-09-14，PATCH）。审计 DEVORDER-AUDIT-2026-09-14 根因修复：version_check.py 删除 24h 节流短路——**每次加载使用 Skill 必查网络**（节流曾导致「平台已发版、本地漏检」事件）；lastcheck 降级为诊断记录；网络异常仍 fail-closed 静默继续。测试用例 2 改为「必查网络」硬断言。引擎三文件零改动（hash 硬闸）。
- `1.4.23`：模型检查层节流移除（2026-09-14，PATCH）。审计 DEVORDER-AUDIT-2026-09-14 根因修复：version_check.py 删除 24h 节流短路——**每次加载使用 Skill 必查网络**（节流曾导致「平台已发版、本地漏检」事件）；lastcheck 降级为诊断记录；网络异常仍 fail-closed 静默继续。测试用例 2 改为「必查网络」硬断言。引擎三文件零改动（hash 硬闸）。
- `1.4.22`：测试版本（2026-09-14，PATCH）。纯 PATCH 版本号升级，内容同 v1.4.21（用于实测第 0 步自动更新链路）。引擎三文件零改动（hash 硬闸）。
- `1.4.21`：SKILL.md 深度压缩 v2（2026-09-14，PATCH）。正文 518→~361 行（-30%）：第 0 步低频段外移 channels.md；红线 5 条合并「红线自检区」18 行（细则外移 output-redlines.md + 不确定先读硬规则）；第 4 步进阶 11 段外移 advanced-consult.md；第 4.5 步呈现契约压缩 77→13 行（7 条渲染硬约束全保留）；场景 2 卡片骨架内嵌第 3 步（41 行逐字节 + 唯一权威标注，免除 templates.md 385 行读取）；detail 压缩 187→104（合并脚本段删除，单源唯一权威 version_check.py）；测试验收段外移 qa-gates.md。引擎三文件零改动（hash 硬闸）。
- `1.4.20`：MCP 适配深度排查修复（2026-09-14，PATCH）。全面排查发现并修复 5 项：① opcs-tools-reference「list_orders/list_bids/select_bid = 接单路径/竞标/中标」口径错误（契约实锤三者均为发单方能力：公共广场/查看报名/选定接单方）；② 同文件错误码表补 3 个服务端新码；③ SKILL.md 补低频工具指针（此前 13 个工具无指引入口，历史 BUG-14/25/26 同类断链）；④ **SKILL.md 补写工具 userConfirmation 硬门禁规则**（服务端 13 个写工具全部强制字面量 true，白名单内 9 个写工具覆盖：create_order/publish_plan/retry_publish/select_bid/review_deliverable/configure_milestones/add_milestone/update_milestone/delete_milestone——此前正文无此规则，属实质安全缺口）；⑤ reference 头部口径同步实测锚定。引擎三文件零改动（hash 硬闸）。
- `1.4.19`：MCP 适配对齐（2026-09-11，PATCH）。工具口径实测锚定——发单方身份面板实测 26/26 与 allowed-tools 集合 diff 零增删零多余（接单方身份可见 17 个属独立接单 Skill）；SKILL.md compatibility/L109 口径升级为「身份可见集」表述；references/opcs-errors.md 补服务端 3 个新错误码（INVALID_ARGUMENT / RESPONSE_SCHEMA_MISMATCH「写操作可能已成功、先只读核对再重试」防重复写 / INTERNAL_ERROR 携 requestId）；constants.json opcs_role_tool_map 完整性维护（issuer 17→26、picker 5→17，只增不删，12 场景核心自检零行为影响）。引擎三文件零改动（hash 硬闸）。
- `1.4.18`：方案甲+丙「确定性脚本化 + ctx 最小集」落地（2026-09-11，PATCH）。工具调用 10→3、模型生成代码 token→0、首轮 ctx 20→12+subtype、第 0 步版本检查脚本化。新增 `scripts/run_gate.py`（闸门单条 CLI + session.json 状态自动读写，拒绝流三态/同类冷却/频率帽语义完整）与 `scripts/version_check.py`（合并版单脚本逐行迁移，输出契约逐字节一致）；SKILL.md 第 2 步改写为参数速查表 + 首轮最小集（危险字段段/按输出执行段原文保留，接单路径边界保留）、第 0 步 4 处「合并脚本」引用收敛；ruff 门禁收编 src/ + scripts/；pytest 69→85（+16 用例）；dist 33→35 文件。引擎三文件零改动（hash 硬闸）。
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
