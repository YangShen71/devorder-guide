# devorder-guide GitHub 开源分发方案·独立评审报告（2026-08-20）

> **评审对象**：`docs/superpowers/plans/2026-08-20-release-v1.md`（方案 A：标准仓库 + INSTALL.md 自安装协议，10 Task / D1-D8 / 23 项修订）
> **评审方式**：独立复核 + 9 工具官方文档/多源联网验证（2026-08-20 实测）+ 与项目既有纪律（红线 G1~G30、check_all 七连、分发一致性）逐条对照
> **评审结论**：方案架构成立且高质量，**工程机制 ≈92 分，生态支持 ≈88 分，客户自助闭环 ≈55 分，综合 ≈82/100**——「可执行，但有两个已知信息错误需修正 + 两个 P0 级补充」
> **置信度声明**：以下所有工具机制均基于 2026-08-20 联网核实的官方文档/官方源，标注「✅已核实」；未实测项标注「未实测」；无臆测。

---

## 一、方案一句话总览

把 devorder-guide 从「内部单目录仓库」改造为 **Agent Skills 标准公开仓库**（`skills/*/SKILL.md` 布局），用 **gh skill / npx skills / 各工具目录扫描** 三通道实现「客户粘贴 GitHub 链接 → AI 自动安装到 9 种主流 AI 工具」，单一内容真源 + 生成镜像 + CI 守卫延续「安装版=源码版」分发纪律。

---

## 二、深度思考：核心机制逐步分析

### Step 1：为什么是「Agent Skills 标准 + skills/*/SKILL.md 布局」（D1）——✅ 验证正确
- **gh skill**（GitHub CLI 2.90+，2026-04-16 公开预览）：官方文档明确「Skills are discovered automatically using the `skills/*/SKILL.md` convention defined by the Agent Skills specification」——**桌面计划 D1 的布局判断与官方规范一致**。
- 支撑证据：`cli.github.com/manual/gh_skill_install` 官方手册（✅ 已核实）。
- **结论**：`skills/devorder-guide/` 做真源是唯一正确的结构；根目录做真源会让 gh skill 发现机制失效。

### Step 2：根 SKILL.md 镜像（D2）——✅ 验证正确
- OpenClaw `openclaw skills install git:owner/repo` 官方要求「Git 和本地安装要求源根目录中存在 SKILL.md」；WorkBuddy「从 Git 仓库导入」同样要求仓库根可识别。
- **结论**：根 SKILL.md = 生成镜像（字节一致 + CI 守卫）设计成立；瘦指针方案（部分工具只读 SKILL.md 单文件会误装）确实不可取。

### Step 3：gh skill 通道（方案主通道）——✅ 验证正确，且覆盖比计划更广
- 官方 `--agent` 支持列表（✅ 已核实，共 40+）：github-copilot / claude-code / cursor / codex / gemini-cli / antigravity / **kimi-cli** / **openclaw** / **trae** / **trae-cn** / codebuddy / amp / cline / devin / goose / opencode / qwen-code / replit 等。
- **关键发现**：官方列表**没有 WorkBuddy 和 InsCode Desktop**（中国本土工具，gh 未收录）——桌面计划把它们放「Git 导入/插件市场」通道是**正确的降级处理**。
- **另一个发现（需修正）**：**TRAE 已被 gh skill 官方支持（--agent trae / trae-cn）**——桌面计划写「TRAE 无法 AI 一键安装，走人工」**已过时**，应改为 `gh skill install <owner>/devorder-guide devorder-guide --agent trae-cn --scope user`。
- 版本解析顺序（官方）：`@TAG` → 默认分支 HEAD；`--pin` 固定。provenance 元数据（source/ref/tree-SHA）写入安装版 frontmatter，支持 `gh skill update`。**与桌面计划 D6 版本体系完全兼容**。

### Step 4：npx skills 通道（skills.sh）——✅ 验证正确
- 官方支持 70+ agent；`npx skills add <owner>/repo -s <skill> -a <agent> -g -y`（-g=global）。桌面计划将其作为 gh 2.90 以下的降级通道，正确。

### Step 5：9 工具原生目录逐项核实（详见 §三 验证表）——✅ 8/9 核实，1 项（InsCode）未验证
- 全部 8 个已核实工具的目录路径与桌面计划**基本一致**，仅 OpenClaw 一处路径语义需修正（见 §四 R2）。

### Step 6：INSTALL.md AI 自安装协议（D8）——✅ 设计成立，依赖两项前提
- 前提 1：目标 AI 工具会读取仓库根 INSTALL.md——成立（README/INSTALL.md 是通用约定）。
- 前提 2：AI 执行安装命令时用户会批准权限确认——正常安全机制，计划已说明。
- **加分项**：GitCode 镜像兜底（国内网络）已在协议内。

### Step 7：install.ps1 / install.sh 万能安装器——✅ 逻辑完整，未实测
- 工具检测（仅安装到已存在目录）+ Python 检测引导 + `-DryRun`。注意 OpenClaw 目标路径需修正（见 R2）。

### Step 8：CI / Release / 版本一致性（D6 + T8）——✅ 逻辑自洽
- pyproject 真源 + SKILL metadata.version + git tag 三者 CI 校验相等；release.yml 在 tag 上先 `--check --tag` 再 `--build`（顺序正确，非空转）。
- **联动收益**：首次 push 到 GitHub 正好触发主仓库 CI 首跑（T2 闭环）——本方案执行即解决 T2 待办。

### Step 9：⚠️ 最大软肋——opcs MCP 客户侧配置（商业闭环关键）
- skill 本体只做「触发判定 + 话术生成」，**发单/接单闭环依赖客户自配 DevOrder MCP（26 工具）**。
- 客户装完 skill 但没有 DevOrder 账号/Key/MCP 配置 → 只能体验「引导」不能「发单」——**这是获客转化的真正分水岭**。
- 计划已诚实声明「MCP 需客户自行配置，本仓库不含凭据」✓，但**缺客户侧引导**：README 需要「如何获取 DevOrder MCP + 配置步骤」的完整指引（或平台提供注册入口链接）。
- **置信度影响**：这是把总分从 90+ 拉到 82 的主要原因。

### Step 10：⚠️ 发布 = 完全公开 = 敏感零容忍
- 公开仓库内容会被 `gh skill search` / `npx skills` 索引，**任何残留价格/刊例/品类手册内容 = 安全事故**。
- 本轮（v0.5.17）已处置 v0.4.md/visual 含敏感参数问题——**发布仓库必须把「敏感扫描」固化为 CI 门禁**（P0 建议，见 R1）。
- 注意：现有 `v0.4-audit/sensitive_scan.py` **本身含明文 P0 词表，不能直接入库**——需写一个「不含词表」的扫描器（词表外置/哈希化），或复用 `--check` 校验产物内零敏感模式。

---

## 三、9+1 工具支持机制验证表（2026-08-20 实测）

| # | 工具 | 用户级目录（已核实） | AI 自装通道 | 验证状态 | 与桌面计划对照 |
|---|---|---|---|---|---|
| 1 | Claude Code | `~/.claude/skills/`（+项目 `.claude/skills/`）| `gh skill --agent claude-code` ✅ / `npx skills` ✅ / 手动复制 | ✅ 官方规范 + 第一手经验 | 一致 ✅ |
| 2 | Codex | `~/.agents/skills/`（旧 `~/.codex/skills/` 兼容）| `gh skill --agent codex` ✅ / `$skill-installer` ✅ / 复制 | ✅ 官方 + 多源 | 一致 ✅ |
| 3 | Cursor | `~/.cursor/skills/`（+兼容 `.agents/.claude/.codex/skills`）| `gh skill --agent cursor` ✅ / 复制（不支持符号链接）| ✅ 官方文档 | 一致 ✅ |
| 4 | Kimi Code | `~/.kimi-code/skills/` **+ `~/.claude/skills/`** + `~/.agents/skills/` | `gh skill --agent kimi-cli` ✅ / 复制 | ✅ 官方文档（确认扫描 ~/.claude/skills）| 一致 ✅ |
| 5 | OpenClaw | workspace `skills/`（默认）或 `--global` → `~/.openclaw/skills` | `openclaw skills install git:owner/repo` ✅ / `gh skill --agent openclaw` ✅ | ✅ 官方 CLI 文档 | ⚠️ **路径需修正**（见 R2）|
| 6 | WorkBuddy | `~/.workbuddy/skills/` | UI「从 Git 仓库导入」✅ / `.skill` ZIP 导入 / 拖拽 | ✅ 第一手经验（本项目即装于此）| 一致 ✅ |
| 7 | TRAE | `~/.trae-cn/skills/`（国内）/ `~/.trae/skills/` | **`gh skill --agent trae/trae-cn` ✅（计划写「人工」已过时）** / 复制 | ✅ gh 官方支持 | ⚠️ **需更新**（见 R3）|
| 8 | InsCode Desktop | AtomCode 规范（`.atomcode-plugin/` 市场目录）| `/plugin marketplace add`（待上架）| ⚠️ **未验证**（依赖 CSDN 内部渠道）| 保守标注 ✅ |
| 9 | GitHub Copilot | gh 自动（project `.github/skills` / user `~/.agents/skills`）| `gh skill --agent github-copilot` ✅ | ✅ 官方文档 | 一致 ✅（顺带）|
| — | npx skills（skills.sh 生态）| 自动映射 70+ agent | `npx skills add ... -a <agent>` ✅ | ✅ 官方 | 一致 ✅ |

> 已验证通道合计 9 条全部真实存在；唯一「未验证」= InsCode（需内部渠道上架后实测）。

---

## 四、关键风险与修正建议（分级）

### 🔴 P0（发布前必须做）

| # | 风险 | 说明 | 处置 |
|---|---|---|---|
| R1 | **发布仓库无敏感扫描门禁** | 公开仓库 = 永久公开；本轮已处置 v0.4 含 ¥ 价格档位问题，但 CI 没有自动防线 | make_artifacts.py `--check` 增加「敏感模式扫描」：扫描 `skills/` + 产物内 `¥|元/|刊例|media_discount|collapse_factor|100-400` 等模式，命中即 exit 1。**词表不能明文入库**（词表本身敏感）→ 用哈希比对或维护在私有处 |
| R2 | **OpenClaw 目标路径错误** | 计划写 `~/.openclaw/workspace/skills/`；官方语义是「当前 workspace 的 skills/ 目录」，`--global` 才是 `~/.openclaw/skills` | install.ps1/install.sh 的 openclaw 目标改 `~/.openclaw/skills`（global 语义）；AI 通道优先用 `openclaw skills install git:<owner>/devorder-guide` |

### 🟠 P1（发布前应做）

| # | 风险 | 说明 | 处置 |
|---|---|---|---|
| R3 | **TRAE 通道信息过时** | 计划写「无法 AI 一键安装」；gh skill 官方已支持 `--agent trae / trae-cn` | INSTALL.md 通道表 + T9 矩阵更新：TRAE = `gh skill install --agent trae-cn` 可用（实测后确认）|
| R4 | **frontmatter 跨工具兼容性未实测** | 当前 `allowed-tools: Bash(python3:*)` 是 Claude 字段；Kimi 规范字段为 type/whenToUse/disableModelInvocation；未知字段是否触发警告未验证 | T9 矩阵必须实测 9 工具 frontmatter 解析；Kimi 需要的 `whenToUse` 已列入 T9 ✓；如 Bash(python3:*) 触发警告 → 评估精简 |
| R5 | **opcs MCP 客户侧引导缺失** | 商业闭环分水岭：客户装完 skill 不知道去哪配 MCP | README 增加「获取 DevOrder MCP 指南」段（注册入口 + 26 工具说明 + 配置步骤），或提供平台引导链接 |
| R6 | **Proprietary 许可与开源惯例张力** | 公开仓库 + 禁止二次分发：fork/PR 场景模糊；gh skill 生态习惯开放许可 | README License 段明确「可免费下载使用；禁止二次分发用于竞争性用途；欢迎 Issue 反馈」，避免误解 |

### 🟡 P2（发布后迭代）

| # | 项 | 说明 |
|---|---|---|
| R7 | 上架申请（anthropics/claude-plugins-community / skills.sh / ClawHub / WorkBuddy SkillHub / InsCode）| 逐个提交，标注状态；InsCode 依赖内部渠道 |
| R8 | 真机验收矩阵（T9）9 工具 × 3 动作 | 发布后 1 周内完成；README/DEV.md 写入实测声明 |
| R9 | 更新机制（gh skill update / 重发链接）| README「更新方式」段 + Issues 模板 |

---

## 五、优缺点详细对照

### 优点

1. **生态标准**：Agent Skills 规范 + gh skill 官方 40+ agent 支持 = 一次改造覆盖主流工具，非各家私有格式。
2. **单一真源防漂移**：`skills/*/SKILL.md` 真源 + 生成镜像 + CI 守卫，延续「安装版=源码版」既有纪律（项目红线 G17 的分发一致性在开源场景的正确延伸）。
3. **AI 自安装协议（创新点）**：客户「粘贴链接 → AI 自动装」把安装门槛降到最低，优于传统「下载 ZIP 手动导入」。
4. **质量门禁自动化**：check_all 七连 + make_artifacts --check/--build + release.yml tag 自动发布 = 发布全程可回退、可审计。
5. **版本三源一致（pyproject/SKILL/tag）**：CI 强制，杜绝 0.5.0/0.3.0/v0.5.15 三套数字并存的历史问题复发。
6. **gh skill provenance**：安装版记录 source/ref/SHA，客户可 `gh skill update` 跟踪上游更新。
7. **联动收益**：发布即触发主仓库 CI 首跑（T2 待办闭环）。
8. **国内网络兜底**：GitCode 镜像已纳入协议。
9. **与既有 v0.5.x 体系零冲突**：目录迁移 + 路径适配的最小改动设计（R2 修订后仅 3 处 check_all 改动）已验证可逆。

### 缺点与风险

1. **opcs MCP 客户侧配置是最大转化瓶颈（R5）**：skill 只解决「引导」，闭环靠客户自配 DevOrder MCP——非开发者客户大概率卡在这一步。
2. **Python 3.10 依赖**：9 工具客户未必有 Python（尤其桌面工具用户）；install.ps1 有检测引导但仍有流失。
3. **frontmatter 兼容性未实测（R4）**：`allowed-tools: Bash(python3:*)` 在非 Claude 工具的行为未知——可能警告、可能忽略、极端情况拒绝解析。
4. **已知信息错误 2 处（R2/R3）**：OpenClaw 路径、TRAE 通道——照原案执行会误导客户或失败。
5. **InsCode 通道不确定性最高**：依赖内部渠道上架，未验证（45 分）。
6. **发布 = 永久公开**：任何敏感残留不可撤回（git 历史永久），需要 P0 扫描门禁 + 发布前人工终检。
7. **Proprietary 许可张力**：开源生态的 fork/PR 惯例与「禁止二次分发」冲突，可能引发误解或社区摩擦。
8. **9 工具真机验收工作量巨大**：T9 矩阵 27 个组合，需真机 + 各工具环境，1 周内完成有压力。
9. **gh skill 为 Public Preview**：命令可能变更（官方注明「可更改」），需在 INSTALL.md 标注版本要求（2.90+）并给 npx 降级通道。

---

## 六、置信度评分（0-100，绝对真实）

| 环节 | 分数 | 依据 |
|---|---|---|
| 方案架构（单一真源+镜像+生成物）| **92** | 与 gh skill/npx skills 官方规范吻合；延续既有纪律；R1~R23 修订后自洽 |
| Claude Code 通道 | **95** | 官方规范 + 项目第一手经验（本技能就在 WorkBuddy/Claude 生态跑通）|
| Codex 通道 | **90** | 官方 + 多源确认（~/.agents/skills / $skill-installer / gh skill）|
| Cursor 通道 | **90** | 官方文档确认（~/.cursor/skills + 兼容 .claude/.codex）|
| Kimi Code 通道 | **88** | 官方确认（~/.kimi-code/skills + ~/.claude/skills + whenToUse 支持）|
| OpenClaw 通道 | **85** | 官方 CLI 确认（install git: 命令）；路径语义需修正（R2）|
| WorkBuddy 通道 | **92** | 第一手经验（本项目安装/使用中）|
| TRAE 通道 | **70** | gh skill 官方支持但未实测；桌面计划信息过时（R3）|
| InsCode Desktop 通道 | **45** | 依赖内部渠道上架，未验证；AtomCode 规范不确定 |
| GitHub Copilot 通道 | **88** | 官方文档确认（gh skill --agent github-copilot）|
| gh skill / npx skills 生态 | **90** | 官方公开预览；命令可能演进（-5 保守）|
| CI / Release / 版本一致性 | **90** | 逻辑自洽，延续既有质量门禁 |
| AI 自安装协议（INSTALL.md）| **85** | 概念成立；依赖 AI 工具行为，实测前 -10 保守 |
| install.ps1 / install.sh | **80** | 逻辑完整；未真机测试多工具（R2 修正后重估）|
| **客户自助闭环（opcs MCP）** | **55** | **最大软肋**：MCP 配置 + Python + 平台账号三重门槛，非开发者客户转化率存疑 |
| **方案综合** | **82** | 加权（架构 90+ / 生态 88+ / 闭环 55 拉低）|

**评分说明**：
- 若完成 R1~R3 修正 + T9 真机矩阵 9/9 通过 + R5 客户引导文档 → 综合可达 **90~93**。
- 若 InsCode 上架成功 + 客户闭环数据验证（真实转化率）→ 可冲击 **95**。
- 在未实测、未上架、未验证客户链路前，**82 是诚实上限**；任何「90+」声明都需要 T9 背书。

---

## 七、结论与下一步

**结论**：方案 A 架构正确、工程质量高，是当前多宿主分发的最优解（对比：多仓各自维护 = 漂移风险；单一 zip 分发 = 无生态发现机制）。**两个已知错误（OpenClaw 路径 / TRAE 通道）+ 一个 P0 缺口（敏感扫描门禁）+ 一个商业缺口（MCP 客户引导）修正后即可执行。**

**建议执行顺序**：
1. **发布前（1 天）**：R1 敏感扫描门禁（词表哈希化）→ R2 OpenClaw 路径 → R3 TRAE 通道更新 → R4 frontmatter 兼容性预案 → R5 README 补 MCP 引导段
2. **发布（1 天）**：owner 决策 → T1~T8 顺序执行（含 CI 首跑）→ T10 v0.6.0 发布 → GitCode 镜像
3. **发布后（1 周）**：T9 真机矩阵 9 工具 → 实测声明写入 README/DEV.md → R7 上架申请 → R9 更新机制

*本报告所有「✅已核实」均基于 2026-08-20 联网官方文档复核；未实测项均已标注，不构成通过声明。*
