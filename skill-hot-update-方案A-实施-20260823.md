# 方案 A 深度优化实施方案：双原生渠道分发 + 全平台版本检查（v2.2 · 约定对齐+双形态打包版）

> **定位**：`skill-hot-update-方案-20260823.md` 方案 A（Claude Code 插件市场 + gh skill）的**可执行落地实施版 v2.2**
> **v2.2 双形态打包（2026-08-24）**：实证发现 dist zip 为**扁平形态**（SKILL.md 在 zip 根），与约定 §1「SKILL.md 必须位于压缩包根目录下的 Skill 目录中」（外层目录形态）冲突——新增 **G7 缺口 + D9 决策（双形态打包）**：公开仓 Release 保持扁平 `.skill`（update.py/Claude 插件/gh skill 消费），平台上架新增外层目录形态 `-upload.zip`（约定 §1 合规）
> **v2.1 约定对齐（2026-08-24）**：依据 `skill-package-generation-guide.md`（Skill 包编写与版本更新约定）全面复审 v2.0，修复 3 项实证发现的约定冲突（frontmatter 顶层 `version`/`identity` 缺失、版本双轨制未说明、发布前检查未对齐），并新增正式「版本更新文件」章节（变更摘要/版本号变更/兼容性/弃用迁移/模块变更记录）
> **v2.0 适配（2026-08-23）**：devorder-guide 公开分发已执行完毕（v0.6.1 已发布、单仓结构就绪、CI 全绿、GitCode 镜像地址定稿）→ v2.0 从 v1.1 的「双仓库 + 独立发布仓」改为「**单仓直接开发 + 三渠道更新 + 全平台版本检查**」，聚焦补齐**双原生渠道真机验证**与 **update.py 全平台版本检查**两块缺口
> **基线**：公开仓 `YangShen71/devorder-guide` v0.6.1（main 分支，tag v0.6.0/v0.6.1，CI 七连全绿，Release 资产自洽）
> **目标版本**：**v0.7.0**（新增 update.py / VERSION 文件 / frontmatter 约定化 / 双形态打包 / 更新指引 / 真机验证——MINOR）
> **日期**：2026-08-24｜**作者**：阳神 + AI 协作
> **覆盖**：Claude Code（T1 autoUpdate）/ Codex 及 40+ CLI（T2 gh skill）/ WorkBuddy（T2 一句话触发 update.py）/ InsCode（T3 手动 + 版本检查）
> **配套纪律**：所有发布声明受红线「实测背书」约束；SKILL.md 变更须跑 hit_check 回归；「引导」二字文案纪律（`grep -c "引导" SKILL.md` = 0）；**约定对齐纪律**（`skill-package-generation-guide.md` 的 §1 包结构 / §2 identity / §3 版本号 / §4~§5 接口 / §6 Harness 更新 / §8 发布前检查）
> **证据标注**：【平台事实】官方文档核验｜【一手实测】本机直接验证｜【推测】未验证推断（2026-08-24 会话实测）

---

## ★ 版本更新文件（v2.0 → v2.2，符合 skill-package-generation-guide.md 约定格式）

> 本文档是「方案 A 实施文档」自身作为版本化交付物的更新说明，格式对齐 `skill-package-generation-guide.md`（§3 版本号 / §4 变更记录风格）。文档版本与 devorder-guide 技能版本**各自独立演进**：本文档 v2.0 → **v2.2**（MINOR×2）；所描述的公开仓技能目标 v0.6.1 → **v0.7.0**（MINOR）；平台线技能版本 **v1.0.0 不变**（见「双轨制」）。

### ★1. 变更摘要（changelog）

**一句话（v2.2）**：按约定 §1 补齐 dist 双形态打包——公开仓 Release 保持扁平 `.skill`，平台上架新增外层目录形态 `-upload.zip`，消除包结构与约定冲突。

**一句话（v2.1）**：按 `skill-package-generation-guide.md` 对齐公开仓 SKILL.md frontmatter（顶层 `version` + `identity`）、明确「平台线/开源线」版本检查双轨制、补发布前检查十项对齐。

**要点**：
- v2.2：🔴 实证发现 dist 扁平形态 ≠ 约定 §1 外层目录形态（G7）→ 双形态打包（D9，已定）；新增 `platform-pack` 子命令；§1「工具 schema 不固化」纪律
- v2.1：修复 3 项实证约定冲突（frontmatter 形态 / 双轨制缺失 / 发布前检查未对齐）+ 新增 G6 缺口 + 3 项实现修订
- 正式化「弃用与迁移指引」与「按模块变更记录」（本章 ★4/★5）

### ★2. 版本号变更说明

| 对象 | 旧版本 | 新版本 | 变更类型 | 依据 |
|---|---|---|---|---|
| 本文档（方案 A 实施） | v2.0 | **v2.2**（v2.1→v2.2 本轮） | MINOR×2（新增约定对齐规则/能力，无破坏性变化） | 约定 §3：新增能力/非破坏性规则 → +0.1.0 |
| 公开仓 devorder-guide | v0.6.1 | **v0.7.0**（目标） | MINOR（update.py + VERSION + frontmatter 约定化 + 双形态打包） | 约定 §3；v2.0 已定 |
| 平台线 devorder-guide | 1.0.0 | **1.0.0**（不变） | 无 | 平台线独立演进，本次不涉及运营端上传 |

**frontmatter 版本号三处一致要求**（约定 §3）：`SKILL.md version` = 运营端上传表单 = Harness `currentVersion`。v0.7.0 起公开仓 SKILL.md 采用顶层 `version`（与平台线一致），上传运营端时**人工确认**两处版本号一致（运营端不自动读包内 version——约定 §3.99 明示）。

### ★3. 兼容性影响说明

| 影响面 | 说明 | 处置 |
|---|---|---|
| SKILL.md frontmatter 形态 | `metadata.version: "0.6.1"`（嵌套）→ 顶层 `version: "0.7.0"` + `identity: CUSTOMER`（约定 §2/§3 形态） | **幂等迁移**：bump 子命令自动处理；迁移前后解析双兼容（S1/S2 修订） |
| **dist 包结构形态（v2.2）** | 现 dist 为**扁平形态**（SKILL.md 在 zip 根）；约定 §1 要求**外层目录形态**（`skill-name/SKILL.md`）；两者消费方不同 | **双形态打包**（D9）：公开仓 Release 扁平 `.skill` 不变（update.py/Claude 插件/gh skill 消费）；平台上架用 `platform-pack` 产出的 `-upload.zip`（外层目录形态，约定 §1 合规） |
| 既有 v0.6.1 安装 | 无 update.py、无顶层 version——`gh skill update`/Claude autoUpdate 读 frontmatter 溯源元数据不受影响（gh skill 注入独立 metadata），版本检查是新增能力 | v0.6.1 → v0.7.0 走三渠道更新（S4 验证）；v0.5.x 需手动升级一次（R9） |
| 平台线（运营端上传） | 平台线版本 1.0.0 与公开仓 0.x **各自独立**；本次不重新上传平台；若上架用 `-upload.zip` 外层目录形态 | SKILL.md 更新段写明双轨制，Harness 走约定接口（§6/§7） |
| CI / 七连 / dist | 零改动；bump 后七连验证的是发布态；`platform-pack` 产物不入库（生成物纪律） | release.sh 顺序不变 |
| 既有用户脚本/工具 | 无已知破坏性变化（方案架构、工具命名、目录结构不变；扁平 .skill 格式不变） | — |

### ★4. 弃用与迁移指引

**弃用清单（v0.7.0 起）**

| 弃用项 | 弃用版本 | 移除计划 | 替代 |
|---|---|---|---|
| frontmatter `metadata.version` 嵌套形态 | v0.7.0 | 解析兜底保留至 v0.8.0（过渡期双兼容），v0.9.0 移除兜底 | 顶层 `version`（约定 §3） |
| 公开仓 SKILL.md 无 `identity` 字段 | v0.7.0 | 同版本补齐（无移除计划——约定 §2 必填） | `identity: CUSTOMER` |
| **扁平形态包直接上架平台线**（v2.2：dist .skill 仅限公开仓自消费） | v0.7.0 | 平台线上架一律用 `-upload.zip` 外层目录形态（约定 §1）；扁平 .skill 永不直传运营端 | `platform-pack` 产物（D9） |
| v1.1「双仓库 + 独立发布仓」设计 | 已在 v2.0 弃用 | 文档 B3 留档备查 | 单仓直接开发 |

**迁移指引（按用户群）**

| 用户群 | 现状 | 迁移动作 | 通道 |
|---|---|---|---|
| 公开仓 v0.6.1 用户 | 已装 v0.6.1（无 update.py） | 无感知升级到 v0.7.0 | Claude autoUpdate（T1）/ `gh skill update`（T2） |
| 旧版用户（v0.5.29/v0.5.26） | 包内无 update.py | **手动升级一次**到 v0.7.0（自举悖论，R9） | INSTALL.md 明示 + Release zip 手动覆盖 |
| 平台线用户 | 已装平台 v1.0.0 | 无动作（平台线独立） | Harness 约定接口自动检查（SKILL.md 更新段） |
| 新用户 | — | 直接装 v0.7.0 | 三渠道任选 |

### ★5. 按模块组织的详细变更记录

| 模块 | 变更类型 | 变更内容 | 对应章节 |
|---|---|---|---|
| 文档头部 | 修改 | 版本 v2.0→v2.2；新增「约定对齐纪律」；证据标注日期更新 | 头部 |
| 方案总览 | 新增 | G6 缺口（frontmatter 与约定冲突，实证）；G7 缺口（dist 扁平形态 vs 约定 §1 外层目录，实证）；0.4 变化表补「约定对齐」「包结构双形态」行；0.1 架构图补平台线 + 双形态标注 | 〇 |
| update.py | 修改 | `local_version()` 双模式正则（顶层 `version` 优先 + `metadata.version` 兜底）；单测补双形态用例；`remote_version()` 注释说明双轨制（平台线不混比） | 二 S1 |
| release_helpers.py | 修改 | `bump` 幂等迁移（检测 metadata 形态自动转顶层 + 插 identity）；`verify` 输出六方口径（+platform-upload 人工确认 warn）；新增 `migrate` 子命令；**v2.2 新增 `platform-pack` 子命令**（扁平 .skill → 外层目录 -upload.zip，约定 §1） | 三 S2 |
| SKILL.md 更新段 | 修改 | 扩展为双段：平台线（约定 §7 最小示例：identity/接口/downloadUrl 不硬编码/校验）+ 开源线（update.py 一句话触发） | 四 S3 |
| 发布前检查 | 新增 | 约定 §8 十项 → 方案 A 落地对照表（S5 步骤 4）；**v2.2 修正第 2 项**（SKILL.md 位于约定目录：平台侧必须外层目录形态） | 六 S5 |
| 版本纪律 | 修改 | 7.1 五方→六方口径（+平台上传人工确认）；7.2 引用约定 §3；新增 frontmatter 形态纪律；**v2.2 新增 7.6 双形态打包纪律 + §1 工具 schema 不固化纪律** | 七 |
| 风险表 | 修改 | 新增 R12（frontmatter 迁移破坏旧解析）/ R13（平台/开源版本线混淆）；**v2.2 新增 R14（包结构形态混淆致平台上架失败）** | 九 |
| 验收清单 | 修改 | 总验收清单补约定对齐验收项；**v2.2 补双形态验收** | 十 |
| 附 A/B | 修改 | 新增 D8 决策（frontmatter 约定化，已定）；**v2.2 新增 D9（双形态打包，已定）**；新增 B5 v2.1 修订记录；**v2.2 新增 B6** | 附 A/B |

---

## 〇、方案总览

### 0.1 目标架构（单仓 + 三渠道 + 一脚本 + VERSION 文件）

```
公开仓 github.com/YangShen71/devorder-guide（main 分支，单仓直接开发 = 唯一权威源）
│  开发即分发：skills/devorder-guide/ 是真源，改完 → 七连 → 打包 → tag
│
├── skills/devorder-guide/             ← 真源（v0.6.1 已就绪）
│   └── scripts/update.py              ← 新增：全平台版本检查/自更新器（随包分发）
├── scripts/make_artifacts.py          ← 已有（扩展：VERSION 同步 + 校验）
├── scripts/release.sh                 ← 新增：一键发布（bump→七连→打包→敏感扫描→五方核对→双推）
├── scripts/sensitive_scan_repo.py     ← 新增（v1.1 设计沿用，防未来误提交）
├── configs/sensitive_lexicon.enc      ← 新增（XOR+Base64 混淆词表，可入库；根 configs/ 与真源隔离）
├── .claude-plugin/marketplace.json    ← 已有（⚠️ source 指向未入库的 plugins/，S0 识别+S4 修复）
├── .atomcode-plugin/marketplace.json  ← 已有（InsCode Desktop 通道）
├── VERSION                            ← 新增：5 字节版本文件（GitCode 降级源 + 五方核对之一）
├── INSTALL.md / README.md             ← 已有（补充：更新机制章节）
└── GitCode 镜像（gitcode.com/YangShen71/devorder-guide）← 双推同步，update.py 降级源

            ┌───────────────┬───────────────────┬───────────────────┐
            ▼               ▼                   ▼                   ▼
      Claude Code      Codex/40+ CLI       WorkBuddy            InsCode
      /plugin 市场       gh skill           AI 一句话触发        Release zip
      autoUpdate=T1     update=T2          update.py=T2        手动重导=T3
      （原生渠道①）       （原生渠道②）        （全平台检查）       （全平台检查）

另：**平台线（运营端上传，v1.0.0）独立并行**——Harness 按 SKILL.md「版本检查与更新」段（约定 §6/§7）调用平台版本查询接口自动更新；update.py 只服务公开仓开源线（GitHub/GitCode），两线版本号各自独立、不混比（详见 S1 双轨制说明）。

**dist 双形态（v2.2，G7/D9）**：
- `devorder-guide.skill`（扁平：SKILL.md 在 zip 根）→ 公开仓 Release，update.py/Claude 插件/gh skill 消费（现状不变）
- `devorder-guide-v{ver}-upload.zip`（外层目录：`devorder-guide/SKILL.md`）→ 平台上架，约定 §1 合规（platform-pack 子命令产出，生成物不入库）
```

### 0.2 阶段划分与依赖关系

| 阶段 | 名称 | 交付物 | 依赖 | 预估 |
|---|---|---|---|---|
| **S0** | 现状盘点与基建补齐 | 已就绪项确认清单、GitCode remote 配置、VERSION 文件机制、plugins/ 缺口修复决策 | 无 | 0.5 天 |
| **S1** | update.py 全平台版本检查 | `scripts/update.py`（--check/--yes/--rollback）+ `tests/test_update.py` | S0 | 1 天 |
| **S2** | 发布管线整合 | `release.sh` 一键八步 + `release_helpers.py`（bump/verify）+ 敏感扫描双脚本 + 五方核对 + GitCode 双推 | S0 | 1 天 |
| **S3** | SKILL.md 更新段 + 用户文档 | SKILL.md「版本检查与更新」段 + INSTALL.md/README 更新机制章节 + hit_check 回归 | S1（可与 S2 并行） | 0.5 天 |
| **S4** | 双原生渠道真机验证 | 三链路实测报告（Claude autoUpdate / gh skill update / WorkBuddy 一句话触发）+ codebuddy 探针结论 | S1+S2+S3 | 1 天 |
| **S5** | v0.7.0 发布与验收 | v0.7.0 Release + 全量验收清单归档 + 可选 gh skill publish | S2+S3+S4 | 0.5 天 |

总计约 **4.5 天**。S1/S2/S3 可两两并行（无文件冲突）；S4 是硬性真机关卡，不可跳过。顺序链：S0→(S1∥S2∥S3)→S4→S5。

### 0.3 现状盘点（2026-08-23 实测，v2.0 的事实基线）

**✅ 已就绪（零改动复用）**

| 资产 | 位置 | 复用方式 |
|---|---|---|
| 真源 `skills/devorder-guide/`（v0.6.1，SKILL.md frontmatter `metadata.version: "0.6.1"` + `whenToUse`） | 公开仓 | 直接作为分发内容，开发即分发；⚠️ **v2.1 实测：frontmatter 为嵌套 `metadata.version` 且无 `identity` 字段——与约定 §2/§3 冲突（见 G6），v0.7.0 迁移** |
| 打包器 `src/package_skill.py`（REQUIRED_TOP 含 SKILL.md/AGENTS.md/pyproject） | 包内 src/ | release.sh 直接调用 |
| 七连门禁 `scripts/check_all.sh`（ruff+pytest+契约审计+命中回归+六位一体+分发自包含） | 包内 scripts/ | release.sh [2/8] 强制执行 |
| `scripts/verify_install.sh`（版本核对 + Zip Slip 防护 + --temp-install） | 包内 scripts/ | update.py 解压防护逻辑移植参考；`--temp-install` 进七连 |
| 产物生成器 `scripts/make_artifacts.py`（--check/--build/--tag，镜像+插件副本+双 marketplace+dist） | 仓库根 scripts/ | 扩展 VERSION 校验；release.sh 调用；⚠️ **v2.2 实证：dist .skill 为扁平形态（SKILL.md 在 zip 根）——与约定 §1 外层目录形态冲突（见 G7），平台侧用 platform-pack 产物** |
| CI 工作流 `ci.yml` + `release.yml`（tag → check_all → --check --tag → build → pytest → gh release create） | .github/workflows/ | 原样保留；release.yml 追加敏感扫描门禁（S2） |
| `.claude-plugin/marketplace.json` + `.atomcode-plugin/marketplace.json`（v0.6.1） | 仓库根 | Claude Code 市场 / InsCode Desktop 通道 |
| 双端单测 `tests/test_mirror.py` / `tests/test_artifacts.py` | 仓库根 tests/ | 原样保留；S1 追加 test_update.py |
| `INSTALL.md`（AI 自安装协议，9 工具通道表）+ `README.md` + install.ps1/install.sh | 仓库根 | S3 追加更新机制章节 |
| GitCode 镜像地址已定稿（`gitcode.com/YangShen71/devorder-guide`，文档/README 已引用） | — | **remote 未配置**（见缺口 G2） |
| 本机真机环境：Claude Code 2.1.169 / gh 2.96.0 / Python 3.14.3 / Node 26.3.0 / WorkBuddy 客户端 | 本机 | S4 验证全部可执行 |

**⚠️ 已识别缺口（v2.0 处理对象）**

| # | 缺口 | 证据 | 处理 |
|---|---|---|---|
| G1 | **marketplace.json 的 `source: "./plugins/devorder-guide"` 指向未入库目录**——`git ls-files plugins` = 0（生成物不入库），CI 因「若存在才校验」全绿，但 Claude Code `/plugin install` 按相对路径找不到插件目录，**市场安装大概率失败** | 一手实测（2026-08-23 git ls-files + make_artifacts.py 源码） | S0 决策修复方案（D6）+ S4 真机验证终审 |
| G2 | **GitCode remote 未配置**（`git remote -v` 仅 origin=GitHub），镜像仓库存在但无双推机制，VERSION 降级源将失效 | 一手实测 | S0 步骤 2 配置 + 发布 SOP 双推固化 |
| G3 | **INSTALL.md / README.md 零更新指引**（grep "更新\|update\|autoUpdate" 零命中）——用户装完不知道如何获取新版 | 一手实测 | S3 补更新机制章节 |
| G4 | **update.py 不存在**，WorkBuddy/InsCode 无任何版本感知能力 | 一手实测（find update.py 空） | S1 全量开发 |
| G5 | **本机三处旧安装**（均无 update.py，S4 自举升级实证基线）：`~/.workbuddy/skills/devorder-guide` = **v0.5.29**、`~/.agents/skills/devorder-guide` = **v0.5.26**、`~/.claude/skills/devorder-guide` = **v0.5.26** | 一手实测（2026-08-23 复核） | S4 作为真机验证基线 |
| G6 | **SKILL.md frontmatter 与约定冲突（v2.1 新增，实证）**：公开仓真源用嵌套 `metadata:\n  version: "0.6.1"`（无顶层 `version`、无 `identity` 字段）；而约定 §2 要求 `identity` 必填、§3 要求顶层 `version`；内部 v1.0.0 已是顶层 `version: 1.0.0` + `identity: CUSTOMER`（形态分裂） | 一手实测（2026-08-24 读公开仓 + 内部 SKILL.md frontmatter） | S1/S2 双形态解析 + 幂等迁移；S3 更新段对齐约定 §7 |
| G7 | **dist 包结构形态与约定 §1 冲突（v2.2 新增，实证）**：`dist/devorder-guide.skill` 为**扁平形态**（zip 根直接含 SKILL.md，27 文件无外层目录）；约定 §1 要求「`SKILL.md` 必须位于压缩包根目录下的 Skill 目录中」（`skill-name/SKILL.md` 外层形态）；两者消费方不同（update.py/Claude/gh skill 认扁平，运营端认外层） | 一手实测（2026-08-24 zipfile 读 dist namelist + 读 package_skill.py 打包逻辑） | S2 双形态打包（D9）：`platform-pack` 子命令产出 `-upload.zip` 外层目录形态；公开仓 .skill 扁平不变 |

### 0.4 v1.1 → v2.0 核心变化

| 维度 | v1.1（草案） | v2.0（适配现状） | 原因 |
|---|---|---|---|
| 仓库架构 | 私有开发仓 + 独立发布仓（双仓库，S0 从零建仓） | **单仓直接开发**（公开仓即唯一开发仓） | T1~T10 已执行完毕，公开仓已集成全部开发资产；v1.1 的 S0/S1 全部过时 |
| 发布管线 | 自研 release.sh 八步 + sensitive_scan 全套 + XOR 词表 | **复用 make_artifacts.py 既有生成/校验**，release.sh 改为编排现有资产 + VERSION 同步 + 双推 | make_artifacts 已承担产物生成与一致性守卫，不重复造轮子 |
| 敏感扫描定位 | 防「私有仓历史敏感推云」+ 防误提交 | **防未来误提交**（公开仓已开源，历史已公开）；release.yml CI 双保险补上 | 定位随仓库状态变化，机制（XOR 混淆 + 全量子串匹配）沿用 v1.1 P0 修复成果 |
| 版本核对 | 四方（SKILL/pyproject/plugin/marketplace） | **五方**（+VERSION 文件） | VERSION 是 GitCode 降级源，必须纳入一致性守卫 |
| update.py 更新源 | 仅 GitHub API（zipball_url 下载） | **GitHub API 主源 + GitCode raw VERSION 降级**；下载改为 **Release 资产 .skill + SHA256 校验**（供应链加固，优于 zipball） | GitCode 镜像已定稿；SHA256 校验解决 v1.1 R5 供应链风险的升级版 |
| 真机验证 | 三链路（Claude/gh skill/codebuddy 探针） | 三链路 + **WorkBuddy 一句话触发** + **marketplace source 修复终审** | 环境已齐备（v1.1 的 R11「本机无 Claude Code」已消除） |
| 版本目标 | v1.0.0 首发冻结 | **v0.7.0**（MINOR）；v1.0.0 推迟到热更新链路真机验证通过后 | 用户决策：v0.7.0 先行验证 |
| GitCode | 二期再议（D4） | **本期启用**（remote + 双推 + 降级源） | 镜像地址已定稿（c83bb7b），国内网络 R4 现实风险 |
| 约定对齐（v2.1） | 未对齐 `skill-package-generation-guide.md`（frontmatter 形态/identity/发布前检查） | **全面对齐**：frontmatter 顶层 version + identity；版本检查双轨制（平台线约定接口 + 开源线 update.py）；发布前检查十项对照表 | 实证发现公开仓 frontmatter 与约定 §2/§3 冲突（G6） |
| 包结构双形态（v2.2） | dist 仅扁平形态（SKILL.md 在 zip 根），平台上架不合规 | **双形态打包**：公开仓扁平 `.skill`（自消费）+ 平台 `-upload.zip` 外层目录形态（约定 §1） | 实证发现 dist 扁平形态与约定 §1 冲突（G7） |

---

## 一、S0 阶段：现状盘点与基建补齐

### 1.1 目标

以「零猜测」原则固话现状基线：逐项核验 0.3 已就绪清单、配置 GitCode remote、设计 VERSION 文件机制、决策 marketplace source 缺口修复方向，为 S1~S5 提供干净起点。

### 1.2 具体操作

**步骤 0：基线核验（对照 0.3 盘点表逐项执行，全部记录到 docs/review/state-baseline-20260823.md）**

```bash
cd /c/Users/阳神71/Desktop/devorder-guide
# ① 版本四方一致确认
grep -E '^version:|^  version:' skills/devorder-guide/SKILL.md    # G6 复证：期望顶层 version 不存在、metadata.version 存在（v2.1 迁移前基线）
grep -m1 '^version' skills/devorder-guide/pyproject.toml         # version = "0.6.1"
python -c "import json;print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"
# ② 分发自包含 + 镜像守卫
bash skills/devorder-guide/scripts/check_all.sh                  # 七连全绿
python scripts/make_artifacts.py --check                         # 一致性通过
# ③ 缺口复证（G1/G2/G3/G4/G5/G6）
git ls-files plugins | wc -l                                     # 期望 0（G1 证据）
git remote -v                                                    # 期望仅 origin（G2 证据）
grep -c "更新" INSTALL.md README.md                              # 期望 0（G3 证据）
find . -name "update.py" -not -path "./.git/*"                   # 期望空（G4 证据）
ls ~/.workbuddy/skills/devorder-guide/SKILL.md                   # 存在（G5 基线）
grep -c '^identity:' skills/devorder-guide/SKILL.md              # G6 复证：期望 0（无 identity 字段）
```

**步骤 1：plugins/ 缺口修复决策（🔴 G1，D6 决策点，S0 必选）**

| 选项 | 操作 | 适用场景 |
|---|---|---|
| **A. source 指向 GitHub Release zip（推荐）** | marketplace.json 的 `plugins[0].source` 改为 `https://github.com/YangShen71/devorder-guide/releases/download/v0.7.0/devorder-guide.skill`（release.sh 每次 bump 时同步写入）；生成物不入库纪律保持不变 | 保持 D1「生成物不入库」；版本语义清晰（source 随版本固定）；Claude Code 从 Release 资产安装【平台事实支持：市场 source 支持 URL】 |
| B. plugins/ 入库 | 修改 .gitignore 移除 `plugins/`，make_artifacts --build 产物直接提交 | 破坏「生成物不入库」纪律；仓库体积增长；CI 校验语义变化 |
| C. 仓库根放 plugin.json | 根 `.claude-plugin/plugin.json` + source `"./"` | v1.1 草案原设计；但根已有 marketplace.json，两文件同目录可行；需真机验证 schema |

> ⚠️ 诚实标注：Claude Code 市场 source 支持 URL 的确切格式【平台事实部分验证，S4 真机终审】——若选项 A 真机安装失败，按报错切换 B/C，**以真机报错为唯一权威**。

**步骤 2：GitCode remote 配置（🔴 G2）**

```bash
cd /c/Users/阳神71/Desktop/devorder-guide
git remote add gitcode https://gitcode.com/YangShen71/devorder-guide.git
git push gitcode main --tags        # 首次双推（v0.6.0/v0.6.1 tag 同步到镜像）
git remote -v                       # 期望：origin(GitHub) + gitcode 双 remote
# 验证镜像可达：git ls-remote gitcode | head -5
```

**步骤 3：VERSION 文件机制设计**

- 位置：仓库根 `VERSION`（GitCode raw URL：`https://gitcode.com/YangShen71/devorder-guide/raw/main/VERSION` 最简）
- 内容：纯版本号一行，无 v 前缀、无换行符以外的内容：`0.7.0`
- 写入时机：仅 release.sh [1/8] bump 时写入（脚本写，禁止手编——生成物纪律）
- 守卫：make_artifacts.py `check_artifacts()` 增加 `VERSION` 与 `version()` 一致性校验（S2 实施）；CI `--check` 自动覆盖

**步骤 4：更新源可达性预检（S1 前置，验证 GitCode raw 可用）**

```bash
# ✅ 已实测（2026-08-23）：GitCode raw GitHub 风格 URL 返回 200；GitHub API releases/latest 可达（tag v0.6.1 + .skill/SHA256SUMS 双资产）
curl -sS --max-time 10 https://gitcode.com/YangShen71/devorder-guide/raw/main/README.md | head -3
# 期望：README 前 3 行（证明 raw 通道 + 镜像同步正常）
curl -sS --max-time 10 -H "User-Agent: devorder-guide-check" https://api.github.com/repos/YangShen71/devorder-guide/releases/latest | head -3
# 本机实测可达；不可达时属网络波动——这正是双源设计的目的
```

### 1.3 涉及文件与配置

| 文件 | 动作 | 说明 |
|---|---|---|
| `.git/config` | 修改 | 新增 gitcode remote |
| `VERSION` | 新建（S2 后由 release.sh 写入；S0 可先手工写 v0.6.1 占位提交） | 5 字节 |
| `docs/review/state-baseline-20260823.md` | 新建 | 基线核验报告（步骤 0 输出归档） |
| `.claude-plugin/marketplace.json` | 修改（D6 决策 A 时） | source → Release zip URL（S4 真机终审前保留 v0.6.1 原样亦可） |

### 1.4 预期结果

- 基线报告落盘，0.3 清单每项有证据
- `git remote -v` 双 remote；镜像 tag 链完整
- VERSION 文件就位且 == 0.6.1
- D6 决策明确并记录

### 1.5 潜在风险及应对

| 风险 | 概率 | 应对 |
|---|---|---|
| GitCode raw 通道不可用（URL 格式与 GitHub 不同） | 中 | S0 步骤 4 预检先行；失败则查 GitCode 文档（GitLab 系 raw 路径 `/raw/<branch>/<file>` 应兼容）；仍不行则降级源改为 GitCode 仓库页 + 人工指引 |
| GitCode push 失败（凭证/网络） | 中 | HTTPS + PAT 预配；`git ls-remote gitcode` 预检；失败记录为环境限制，不阻塞其他阶段（GitHub 仍是权威源） |
| marketplace source 改动引入 schema 不兼容 | 中 | D6 三选项以 S4 真机报错为准，准备回退路径（git revert marketplace.json） |
| 首次双推把本地未发布提交带上镜像 | 低 | push 前 `git status` 确认工作区干净；双推顺序固定 origin 先、gitcode 后 |

### 1.6 验收清单

- [ ] 基线报告落盘，含步骤 0 全部命令输出粘贴
- [ ] `git ls-files plugins` = 0 已复证并记录为 G1 证据
- [ ] D6 决策已明确（A/B/C 三选一，建议 A）
- [ ] `git remote -v` 含 gitcode；`git push gitcode main --tags` 成功；镜像 v0.6.0/v0.6.1 tag 可见
- [ ] `VERSION` 文件内容 = `0.6.1`
- [ ] GitCode raw README 预检返回内容（证明降级源通道可用）

---

## 二、S1 阶段：update.py 全平台版本检查开发

### 2.1 目标

技能自带 `update.py`：任何宿主（CLI / Web 平台 / WorkBuddy / InsCode）可通过一句话触发版本检查（--check，只读）；WorkBuddy 等可写目录的宿主可一键更新（--yes，显式确认 + SHA256 校验 + 失败自动回滚）；--rollback 恢复最近备份。

### 2.2 具体操作

**步骤 1：编写 `skills/devorder-guide/scripts/update.py`（随 dist 分发，零第三方依赖）**

> v2.0 相对 v1.1 的两处实质优化：① 远端版本**双源**（GitHub API 主源 + GitCode raw VERSION 降级）；② 下载对象从 zipball 改为 **Release 资产 `devorder-guide.skill` + SHA256SUMS 校验**（供应链加固：内容由 CI 生成 + 哈希比对，替代 v1.1 仅 zipball 的方案）。
>
> v2.1 修订（约定对齐）：③ `local_version()` 改为**双模式正则**——顶层 `version` 优先（约定 §3 形态，v0.7.0 起），`metadata.version` 嵌套兜底（v0.6.1 及旧形态过渡期，v0.9.0 移除）；④ 明确**双轨制**：update.py 只服务公开仓开源线（GitHub/GitCode 版本号 0.x），**平台线（运营端上传 v1.0.0）由 SKILL.md「版本检查与更新」段承载**（约定 §6/§7 接口），两线版本号各自独立、不混比——避免平台 1.x 与开源 0.x 误报更新。

```python
#!/usr/bin/env python3
"""update.py — devorder-guide 版本检查与自更新（随技能包分发，零第三方依赖）

用法：
  python scripts/update.py --check      # 只读检查（无任何写操作）
  python scripts/update.py --yes        # 执行更新（写操作，须用户显式确认）
  python scripts/update.py --rollback   # 回滚到最近一次备份（.bak-*）
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

OWNER, REPO = "YangShen71", "devorder-guide"
GITHUB_API = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
GITCODE_VER = f"https://gitcode.com/{OWNER}/{REPO}/raw/main/VERSION"
ROOT = Path(__file__).resolve().parent.parent          # 技能根目录
UA = {"User-Agent": "devorder-guide-update/0.7"}       # GitHub API 无 UA 直接 403
TIMEOUT = 10                                           # 秒/请求


def skill_version(text: str) -> str | None:
    """从 SKILL.md frontmatter 解析版本号。双模式（v2.1 约定对齐）：
    ① 顶层 version（约定 §3 形态，v0.7.0 起）优先；② metadata.version 嵌套（v0.6.1 旧形态）兜底。
    🔴 顺序不可反：顶层优先，否则 metadata 兜底永不触发（无顶层时才能匹配嵌套）。"""
    for pat in (
        r"(?m)^version:\s*[\"']?([0-9]+(?:\.[0-9]+)*)",
        r"^metadata:\s*$.*?^\s+version:\s*[\"']?([0-9]+(?:\.[0-9]+)*)",
    ):
        m = re.search(pat, text, re.M | re.S)
        if m:
            return m.group(1)
    return None


def local_version() -> str:
    v = skill_version((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    assert v, "SKILL.md 找不到 version（顶层或 metadata.version）"
    return v


def ver_tuple(v: str) -> tuple:
    """语义化版本 → int 元组。🔴 必须转 int：字符串比较会把 0.10.0 误判小于 0.9.0。"""
    m = re.match(r"(\d+(?:\.\d+)*)", v or "")
    return tuple(int(p) for p in m.group(1).split(".")) if m else (0,)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def remote_version() -> tuple | None:
    """双源取远端版本，返回 (version, source)；全失败返回 None。"""
    try:  # 主源：GitHub API releases/latest
        data = json.loads(fetch(GITHUB_API))
        return data["tag_name"].lstrip("v"), "github"
    except Exception:
        pass
    try:  # 降级源：GitCode raw VERSION（镜像仓库，git push 自动同步）
        return fetch(GITCODE_VER).strip(), "gitcode"
    except Exception:
        return None


def _sha256_ok(zip_path: Path, sums: str) -> bool:
    expect = None
    for line in sums.splitlines():
        if line.strip().endswith("devorder-guide.skill"):
            expect = line.split()[0].lower()
    if not expect:
        return False
    actual = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return actual == expect


def do_update() -> int:
    remote = remote_version()
    if remote is None:
        print("⚠️ 检查失败（GitHub 与 GitCode 均不可达），当前保持 v" + local_version() + "，可稍后重试或手动下载 Release zip")
        return 1
    rv, src = remote
    lv = local_version()
    if ver_tuple(rv) <= ver_tuple(lv):
        print(f"✅ 已是最新：本地 v{lv} / 远端 v{rv}（源：{src}）")
        return 0
    print(f"ℹ️ 发现新版：本地 v{lv} → 远端 v{rv}（源：{src}）")
    if "--yes" not in sys.argv:
        print("ℹ️ 这是只读检查。确认更新请执行：python scripts/update.py --yes（将下载、校验并原子替换）")
        return 0
    # ── 写操作：显式确认门禁已由调用方（宿主 AI）把关 ──
    if not os.access(ROOT, os.W_OK):
        print("❌ 技能目录不可写（本环境不支持自动更新），请手动下载 Release zip 覆盖安装")
        return 0
    try:  # 下载 Release 资产 .skill + SHA256SUMS（主源 GitHub；失败告知手动）
        api = json.loads(fetch(GITHUB_API))
        tag = api["tag_name"]
        url_zip = url_sum = None
        for a in api.get("assets", []):
            if a["name"] == "devorder-guide.skill":
                url_zip = a["browser_download_url"]
            if a["name"] == "SHA256SUMS":
                url_sum = a["browser_download_url"]
        if not url_zip or not url_sum:
            print("❌ Release 资产不完整（缺 .skill 或 SHA256SUMS），中止更新")
            return 1
        tmp = Path(tempfile.mkdtemp(prefix="devorder-guide-update-"))
        try:
            zip_path = tmp / "devorder-guide.skill"
            zip_path.write_bytes(urllib.request.urlopen(urllib.request.Request(url_zip, headers=UA), timeout=TIMEOUT).read())
            sums = fetch(url_sum)
            if not _sha256_ok(zip_path, sums):
                print("❌ SHA256 校验失败（下载内容被篡改或损坏），中止更新")
                return 1
            # Zip Slip 防护解压（移植 verify_install.sh 逻辑）
            extract = tmp / "pkg"
            with zipfile.ZipFile(zip_path) as z:
                for name in z.namelist():
                    if name.endswith("/"):
                        continue
                    parts = Path(name).parts
                    if any(p == ".." for p in parts) or Path(name).is_absolute():
                        print(f"❌ Zip Slip 拦截：{name}")
                        return 1
                    target = extract.joinpath(*parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(name))
            # 校验：SKILL.md 存在 + 版本 == 远端 + 关键文件齐备
            pkg_skill = extract / "SKILL.md"
            if not pkg_skill.exists():
                print("❌ 新包缺 SKILL.md，中止更新")
                return 1
            pkg_v = skill_version(pkg_skill.read_text(encoding="utf-8"))
            if pkg_v != rv:
                print(f"❌ 新包版本校验失败（新包 v{pkg_v} ≠ 远端 v{rv}），中止更新")
                return 1
            for key in ("src/guide_gate.py", "configs/constants.json", "references/category-enum.md", "scripts/update.py"):
                if not (extract / key).exists():
                    print(f"❌ 新包缺关键文件 {key}，中止更新")
                    return 1
            # 原子替换：技能目录 → .bak-{lv}-{ts}；新包移入；失败自动恢复
            bak = ROOT.with_name(f"{ROOT.name}.bak-{lv}-{int(time.time())}")
            shutil.move(str(ROOT), str(bak))
            try:
                shutil.move(str(extract), str(ROOT))
            except Exception as e:
                try:
                    shutil.move(str(bak), str(ROOT))  # 回滚
                    print(f"❌ 替换失败（{e}），已回滚旧版")
                except Exception:
                    print(f"❌ 替换失败且回滚失败：技能目录现位于 {bak}，请手动恢复")
                return 1
            print(f"✅ 已更新至 v{rv}（旧版备份于 {bak.name}；源：{src}）")
            return 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        print(f"⚠️ 更新失败：{e}；当前保持 v{lv}，可稍后重试或手动下载 Release zip")
        return 1


def do_rollback() -> int:
    baks = sorted(ROOT.parent.glob(f"{ROOT.name}.bak-*"))
    if not baks:
        print("ℹ️ 无可用备份，无法回滚")
        return 0
    latest = baks[-1]
    # 先挪走当前（不删除）→ 恢复备份 → 成功才丢弃当前版；失败恢复当前版，不丢数据
    swap = ROOT.with_name(f"{ROOT.name}.swap-{int(time.time())}")
    shutil.move(str(ROOT), str(swap))
    try:
        shutil.move(str(latest), str(ROOT))
        shutil.rmtree(swap, ignore_errors=True)  # 回滚成功，丢弃当前版
    except Exception as e:
        shutil.move(str(swap), str(ROOT))  # 回滚失败，恢复当前版
        print(f"❌ 回滚失败（{e}），已恢复当前版本")
        return 1
    print(f"✅ 已回滚（备份 {latest.name} 已恢复）；当前版本 v{local_version()}")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if cmd == "--rollback":
        return do_rollback()
    return do_update()


if __name__ == "__main__":
    sys.exit(main())
```

> 说明：`--yes` 与 `--check` 共用 `do_update()`——`--check` 到「发现新版」即停（只读）；`--yes` 继续写操作。网络失败/校验失败均 exit 1 且**不改任何文件**（断网降级安全）。

**步骤 2：单测 `tests/test_update.py`（TDD：先写测试后实现）**

```python
"""update.py 单测：版本解析/比较/失败路径（不入包，仓库根 tests/）"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("update", Path(__file__).resolve().parents[1] / "skills/devorder-guide/scripts/update.py")
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)


def test_ver_tuple_semantic():
    # 🔴 字典序陷阱回归：0.10.0 必须大于 0.9.0
    assert up.ver_tuple("0.10.0") > up.ver_tuple("0.9.0")
    assert up.ver_tuple("0.7.0") > up.ver_tuple("0.6.1")
    assert up.ver_tuple("1.0.0") > up.ver_tuple("0.7.0")
    assert up.ver_tuple("0.7.0") == up.ver_tuple("0.7.0")


def test_ver_tuple_handles_suffix():
    # pre-release 后缀（如 0.7.0-rc1）只取数字前缀
    assert up.ver_tuple("0.7.0-rc1") == up.ver_tuple("0.7.0")
    assert up.ver_tuple("garbage") == (0,)


def test_local_version_parses_frontmatter():
    # 真实 SKILL.md 的版本号可解析（顶层 version 优先）
    v = up.local_version()
    assert v.count(".") == 2 and v[0].isdigit()


def test_skill_version_top_level_first():
    # v2.1 约定对齐：顶层 version（约定 §3 形态）优先于 metadata.version
    assert up.skill_version("---\nversion: 0.7.0\nmetadata:\n  version: \"0.6.1\"\n---") == "0.7.0"


def test_skill_version_metadata_fallback():
    # v0.6.1 旧形态兜底（过渡期双兼容，v0.9.0 移除兜底）
    assert up.skill_version("---\nname: devorder-guide\nmetadata:\n  version: \"0.6.1\"\n---") == "0.6.1"
    assert up.skill_version("---\nname: devorder-guide\n---") is None
```

**步骤 3：接入 CI 与发布门禁**

七连（check_all.sh）**不含 pytest**（七连 = ruff check / ruff format / 核心自检 / 契约审计 / 命中回归 / 六位一体 / 分发一致性）；pytest 由 ci.yml/release.yml 单独执行 `python -m pytest tests/ -v`——新增 test_update.py 自动纳入（tests/ 在仓库根），**CI 层零改动**。release.sh 在 [2/8] 七连之后补跑一次 pytest（本地发布也验证单测）：

### 2.3 涉及文件与配置

| 文件 | 动作 |
|---|---|
| `skills/devorder-guide/scripts/update.py` | 新建（~160 行，随 dist 分发） |
| `tests/test_update.py` | 新建（5 个测试函数：版本比较 ×2 / 真实 frontmatter ×1 / 双形态解析 ×2） |
| `scripts/make_artifacts.py` | 零改动（update.py 在包内 scripts/，随 _sync_dir 自动进插件副本与 dist） |

### 2.4 预期结果

- `--check` 双源实测：GitHub 可达时报 github 源；断网/被墙时自动降级 gitcode 源；全失败报「检查失败」exit 1
- `--yes` 完成「下载 .skill → SHA256 校验 → Zip Slip 防护解压 → 版本/关键文件校验 → 原子替换 + .bak 备份」闭环
- 双形态 frontmatter 解析实测：顶层 version（新）与 metadata.version（旧）均可解析（v2.1）
- pytest 数量 5 → 10（现有 test_mirror 2 + test_artifacts 3，新增 test_update 5）

### 2.5 潜在风险及应对

| 风险 | 概率 | 应对 |
|---|---|---|
| GitHub API 限流（60 次/时/IP） | 低 | 检查频次天然低（用户主动问才查）；降级源兜底；不引入缓存复杂度 |
| GitCode raw 与 GitHub raw 行为差异 | 中 | S0 步骤 4 预检；单测不依赖网络（版本比较纯函数），网络路径真机验收 |
| `--yes` 时 GitHub API 可达但资产 URL 被墙（browser_download_url 走 github.com） | 中 | 下载失败 → 「请手动下载 Release zip」exit 1（如实告知）；GitCode 资产下载列为二期增强（附 A D7） |
| update.py 自举悖论（旧版包内无 update.py 的 v0.5.29 用户） | **高（结构性）** | 诚实披露：**v0.7.0 起才随包分发 update.py，旧版本用户需手动升级一次**（INSTALL.md 写明）；S4 用 WorkBuddy 已装 v0.5.29 实证此路径 |
| AI 主动执行 --check 的遵循度不稳定 | 高 | SKILL.md 用确定性指令（「用户说 X 时执行 Y」）；不依赖主动检查为唯一入口（S3） |

### 2.6 验收清单

- [ ] `pytest tests/test_update.py` 5 用例全过（含 0.10.0 > 0.9.0 字典序回归、顶层 version 优先、metadata.version 兜底）
- [ ] `python skills/devorder-guide/scripts/update.py --check` 有网络：输出「本地 v0.6.1 / 远端 vX.Y.Z（源：github）」
- [ ] 断网实验（临时断网 / 改 hosts 显式构造——本机 GitHub API 实测可达，不可达场景不能靠偶然网络波动覆盖）：输出「⚠️ 检查失败…」exit 1，不崩溃、不改文件
- [ ] 本地版本人为调低 → `--yes` 更新成功 → SKILL.md version == 远端版本
- [ ] `.bak-{旧版本}-{时间戳}` 备份目录存在
- [ ] `--rollback` 恢复旧版成功
- [ ] **SHA256 篡改实验**：下载后人为改写 .skill 字节（或伪造 SHA256SUMS）→ 校验拦截，不替换
- [ ] **坏包实验**：Release 资产换成缺 SKILL.md 的坏包 → 校验失败 → 中止，本地版本不变
- [ ] **Zip Slip 实验**：构造含 `../` 路径的 zip → 拦截
- [ ] **只读目录实验**：技能目录设只读 → 「不支持自动更新」exit 0
- [ ] **双形态实验**：SKILL.md 分别用顶层 version 与 metadata.version 两种形态 → `--check` 均能报正确本地版本（v2.1）
- [ ] `pytest` 总数 5 → 10 全绿（CI `python -m pytest tests/ -v` 自动纳入 test_update.py）

---

## 三、S2 阶段：发布管线整合

### 3.1 目标

一条命令完成「bump（含 frontmatter 约定化迁移）→ 七连 → 打包 → 敏感扫描 → 五方核对（+平台上传人工确认=六方口径）→ tag → GitHub+GitCode 双推」，复用既有 make_artifacts/CI 资产，杜绝手工发布的漂移与泄漏风险。

### 3.2 具体操作

**步骤 1：`scripts/release_helpers.py`（发布逻辑，纯 Python 跨平台；v1.1 设计沿用，删掉 sync 子命令——单仓无发布仓可同步；v2.1 新增 frontmatter 幂等迁移与六方核对）**

```python
#!/usr/bin/env python3
"""release_helpers.py — 发布管线子命令（release.sh 调用，也可独立执行）

用法：
  python scripts/release_helpers.py bump <root> <new_ver>       # SKILL.md + pyproject + VERSION 同步 bump（含 frontmatter 幂等迁移）
  python scripts/release_helpers.py migrate <root>              # 仅执行 frontmatter 约定化迁移（顶层 version + identity），不 bump（可选显式执行）
  python scripts/release_helpers.py market-source <root> <ver>  # 双 marketplace source → Release zip URL（D6 决策 A）
  python scripts/release_helpers.py platform-pack <root> <ver>  # 双形态打包（v2.2/G7/D9）：扁平 .skill → 外层目录 -upload.zip（约定 §1 形态）
  python scripts/release_helpers.py verify <root>               # 五方版本硬核对 + 平台上传版本人工确认（六方口径）
"""
import json, re, shutil, sys, tempfile, zipfile
from pathlib import Path

VERSION_FILE = "VERSION"   # 仓库根，GitCode 降级源


def skill_version(text: str) -> str | None:
    """双模式版本解析（与 update.py 同构，v2.1 约定对齐）：
    顶层 version（约定 §3）优先；metadata.version 嵌套（旧形态）兜底。"""
    for pat in (
        r"(?m)^version:\s*[\"']?([0-9]+(?:\.[0-9]+)*)",
        r"^metadata:\s*$.*?^\s+version:\s*[\"']?([0-9]+(?:\.[0-9]+)*)",
    ):
        m = re.search(pat, text, re.M | re.S)
        if m:
            return m.group(1)
    return None


def migrate_frontmatter(skill_path: Path, new_ver: str | None = None) -> tuple[bool, str]:
    """frontmatter 约定化迁移（幂等，v2.1）：
    ① 无顶层 version → 从 metadata.version 迁移为顶层 version（约定 §3 形态）；
    ② 无 identity → 补 identity: CUSTOMER（约定 §2 必填）。
    返回 (是否发生变更, 说明)。重复执行安全（已迁移则零变更）。"""
    text = skill_path.read_text(encoding="utf-8")
    orig = text
    if re.search(r"(?m)^version:", text) is None:  # 无顶层 version → 迁移嵌套块为顶层
        text = re.sub(r'^metadata:\s*$\n^\s+version:\s*["\']?[0-9.]+["\']?\s*$\n?', "", text, count=1, flags=re.M)
        ver = new_ver or (skill_version(orig) or "0.0.0")
        text = text.replace("---\n", f'---\nversion: "{ver}"\n', 1)
    if re.search(r"(?m)^identity:", text) is None:  # 无 identity → 补约定 §2 必填字段
        # 插到 name 之后（frontmatter 第 2 行），保持 YAML 合法
        if re.search(r"(?m)^name:", text):
            text = re.sub(r"(?m)(^name:[^\n]*\n)", r"\1identity: CUSTOMER\n", text, count=1)
        else:
            text = text.replace("---\n", "---\nidentity: CUSTOMER\n", 1)
    if text != orig:
        skill_path.write_text(text, encoding="utf-8")
        return True, "frontmatter 已迁移（顶层 version + identity: CUSTOMER）"
    return False, "frontmatter 已是约定形态（零变更）"


def bump(root: Path, new_ver: str):
    changed, note = migrate_frontmatter(root / "skills/devorder-guide/SKILL.md", new_ver)
    targets = [
        # SKILL.md：顶层 version 行（迁移后固定带双引号格式）
        ("skills/devorder-guide/SKILL.md",
         r'(?m)^version:\s*"([0-9.]+)"',
         lambda m: f'version: "{new_ver}"'),
        ("skills/devorder-guide/pyproject.toml",
         r'(^version\s*=\s*")[0-9.]+(")',
         lambda m: m.group(1) + new_ver + m.group(2)),
        (VERSION_FILE,
         r'(^)[0-9.]+($)',
         lambda m: m.group(1) + new_ver + m.group(2)),
    ]
    for rel, pat, repl in targets:
        p = root / rel
        text = p.read_text(encoding="utf-8")
        text2 = re.sub(pat, repl, text, count=1, flags=re.M)
        assert text2 != text, f"{rel} 版本未变化（该处已为 {new_ver}？）"
        p.write_text(text2, encoding="utf-8")
    print(f"✅ bump → {new_ver}（SKILL.md + pyproject + VERSION；{note}）")


def migrate(root: Path):
    changed, note = migrate_frontmatter(root / "skills/devorder-guide/SKILL.md")
    print(f"✅ migrate：{note}")
    if changed:
        print("ℹ️ 变更已写入，建议先跑 check_all + hit_check 验证，再进入 bump")


def market_source(root: Path, new_ver: str):
    """D6 决策 A：双 marketplace.json 的 plugins[0].source → Release zip URL（版本化）。
    🔴 必须同步两处（.claude-plugin 与 .atomcode-plugin 为同一文件的两份拷贝）；文件缺失时 json.load 抛错，set -e 捕获即停。"""
    for rel in (".claude-plugin/marketplace.json", ".atomcode-plugin/marketplace.json"):
        p = root / rel
        data = json.loads(p.read_text(encoding="utf-8"))
        data["plugins"][0]["source"] = f"https://github.com/YangShen71/devorder-guide/releases/download/v{new_ver}/devorder-guide.skill"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ marketplace source → v{new_ver} Release zip（双 marketplace 同步）")


def platform_pack(root: Path, ver: str):
    """双形态打包（v2.2，G7/D9）：
    dist/devorder-guide.skill（扁平，SKILL.md 在 zip 根）→ dist/devorder-guide-v{ver}-upload.zip（外层目录 devorder-guide/SKILL.md，约定 §1 形态）。
    🔴 平台线上架必须用本子命令产物——扁平形态直接上传不合规（约定 §1：SKILL.md 必须位于压缩包根目录下的 Skill 目录中）。
    产出物不入库（生成物纪律）。"""
    src = root / "dist/devorder-guide.skill"
    assert src.exists(), f"缺扁平包 {src}（先跑 [3/8] make_artifacts --build）"
    target = root / f"dist/devorder-guide-v{ver}-upload.zip"
    tmp = Path(tempfile.mkdtemp(prefix="platform-pack-"))
    try:
        with zipfile.ZipFile(src) as z:
            for name in z.namelist():
                if name.endswith("/"):
                    continue
                parts = Path(name).parts
                if any(p == ".." for p in parts) or Path(name).is_absolute():
                    sys.exit(f"❌ Zip Slip 拦截：{name}")
                out = tmp.joinpath(*parts)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(z.read(name))
        assert (tmp / "SKILL.md").exists(), "扁平包内缺 SKILL.md（形态异常）"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(tmp.rglob("*")):
                if p.is_file():
                    zf.write(p, f"devorder-guide/{p.relative_to(tmp)}")  # 外层目录前缀（约定 §1）
        print(f"✅ platform-pack → {target.relative_to(root)}（外层目录形态，{sum(1 for _ in zipfile.ZipFile(target).namelist())} 文件）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verify(root: Path):
    def read(p: Path):
        return p.read_text(encoding="utf-8") if p.exists() else ""
    def ver_of(text, pattern, flags=0):
        m = re.search(pattern, text, flags)
        return m.group(1) if m else "UNKNOWN"
    versions = {
        "pyproject": ver_of(read(root / "skills/devorder-guide/pyproject.toml"), r'^version\s*=\s*"?([0-9.]+)', re.M),
        "SKILL.md": skill_version(read(root / "skills/devorder-guide/SKILL.md")) or "UNKNOWN",
        "plugin.json": json.loads(read(root / "plugins/devorder-guide/.claude-plugin/plugin.json") or "{}").get("version", "UNKNOWN"),
        "marketplace": json.loads(read(root / ".claude-plugin/marketplace.json") or "{}")["plugins"][0]["version"],
        "VERSION": read(root / VERSION_FILE).strip() or "UNKNOWN",
    }
    print(" · ".join(f"{k}={v}" for k, v in versions.items()))
    assert len(set(versions.values())) == 1 and "UNKNOWN" not in versions.values(), "❌ 五方版本不一致！"
    print("✅ 五方一致")
    print("⚠️ 六方口径：平台上传表单版本（= 运营端 /api/v1/skills/version 响应的 currentVersion）须人工确认 == 上述五方（约定 §3.99：运营端不自动读包内 version，identity + version 不允许重复上传）")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "bump": bump(Path(sys.argv[2]), sys.argv[3])
    elif cmd == "migrate": migrate(Path(sys.argv[2]))
    elif cmd == "market-source": market_source(Path(sys.argv[2]), sys.argv[3])
    elif cmd == "platform-pack": platform_pack(Path(sys.argv[2]), sys.argv[3])
    elif cmd == "verify": verify(Path(sys.argv[2]))
```

> ⚠️ 注意：`verify` 读 `plugins/devorder-guide/.claude-plugin/plugin.json`——该文件是 make_artifacts --build 的生成物（不入库），release.sh 顺序保证 [3/8] build 在 [6/8] verify 之前。

**步骤 2：`scripts/release.sh`（一键发布八步，v2.0 单仓版）**

```bash
#!/usr/bin/env bash
# release.sh — 一键发布八步（单仓版）
# 用法：bash scripts/release.sh <new-version>
set -euo pipefail

NEW_VER="${1:?用法: bash scripts/release.sh <new-version>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python}"

echo "[1/8] 版本 bump（SKILL.md + pyproject + VERSION；含 frontmatter 幂等迁移为顶层 version + identity）..."
"${PYTHON}" scripts/release_helpers.py bump "${ROOT}" "${NEW_VER}"

echo "[2/8] 质量门禁（七连，验证发布态）+ 单测（pytest 不入七连，单独跑）..."
bash skills/devorder-guide/scripts/check_all.sh
"${PYTHON}" -m pytest tests/ -v || { echo "❌ pytest 失败——本地请确认解释器含 pytest（check_all 的 managed venv 自带），或用 PYTHON=<venv 路径> bash scripts/release.sh <ver>"; exit 1; }

echo "[3/8] 生成分发产物（make_artifacts --build）+ 双形态打包（platform-pack，约定 §1 外层目录形态）..."
"${PYTHON}" scripts/make_artifacts.py --build
"${PYTHON}" scripts/release_helpers.py platform-pack "${ROOT}" "${NEW_VER}"

echo "[4/8] 敏感扫描（fail-closed，XOR 混淆词表全量子串匹配）..."
"${PYTHON}" scripts/sensitive_scan_repo.py "${ROOT}"

echo "[5/8] marketplace source 版本化（D6 决策 A；决策 B/C 时注释本行）..."
"${PYTHON}" scripts/release_helpers.py market-source "${ROOT}" "${NEW_VER}"

echo "[6/8] 五方版本核对 + make_artifacts --check --tag（硬校验；平台上传版本人工确认=六方口径）..."
"${PYTHON}" scripts/release_helpers.py verify "${ROOT}"
"${PYTHON}" scripts/make_artifacts.py --check --tag "v${NEW_VER}"

echo "[7/8] 提交 + tag + 双推（GitHub 权威 + GitCode 镜像）..."
git add -A
git commit -m "release: v${NEW_VER}（热更新机制）" || echo "ℹ️ 无变更可提交"
git tag "v${NEW_VER}"
git push origin main --tags
git push gitcode main --tags || echo "⚠️ GitCode 推送失败（不阻断——GitHub 仍是权威源，GitCode 可稍后补推）"

echo "[8/8] 等待 release.yml 出 Release + 资产..."
gh run list --limit 3 --json status,headBranch,event 2>/dev/null | head -5 || echo "ℹ️ gh 未认证/网络失败，跳过 run 检查（Release 是否生成以 GitHub 页面为准）"
echo "🎉 v${NEW_VER} 发布完成（Claude autoUpdate / gh skill update / update.py 三渠道待生效）"
```

**步骤 3：敏感扫描（v1.1 设计沿用，XOR 混淆词表 + 运行时全量子串匹配）**

- `scripts/sensitive_scan_repo.py`（目录版，~80 行）：读 `configs/sensitive_lexicon.enc` → XOR+Base64 解码 → 对工作区文本文件做「任一词表项 in text」全量子串匹配（大小写不敏感预折叠）→ 命中打印（文件名 + sha256 前 8 位，不回显原文）→ exit 1
- 🔴 **扫描范围必须排除生成物与二进制**：`.git/`、`dist/`、`plugins/`、`__pycache__/`、`.pytest_cache/`、`*.skill`——否则 .git 对象等二进制压缩数据可能误命中词条（如价格数字串），fail-closed 误杀发布（v2.0 复审发现，扫描器内置排除清单）
- 词表来源：`C:\skill-development\devorder-guide-workspace\v0.4-audit\` 现有 P0 词表改造（该目录**永不入库**）；生成脚本 `gen_lexicon.py` 留在内部
- 入库文件：`scripts/sensitive_scan_repo.py` + `configs/sensitive_lexicon.enc`（混淆存储，grep 不可见明文）
- CI 双保险：release.yml 追加扫描步骤（tag 触发时扫描整个 checkout）

**步骤 4：release.yml 追加敏感扫描门禁**

```yaml
      - name: 敏感扫描门禁（CI 双保险，XOR 混淆词表全量匹配）
        run: python scripts/sensitive_scan_repo.py .
```

（追加在 `make_artifacts.py --check --tag` 之前——先扫描后发布，fail-closed）

### 3.3 涉及文件与配置

| 文件 | 动作 |
|---|---|
| `scripts/release_helpers.py` | 新建（bump 含 VERSION + frontmatter 幂等迁移；migrate 子命令；market-source；platform-pack 双形态打包；verify 五方硬核对 + 平台人工确认六方口径） |
| `scripts/release.sh` | 新建（八步编排） |
| `scripts/sensitive_scan_repo.py` + `configs/sensitive_lexicon.enc` | 新建（可入库） |
| `.github/workflows/release.yml` | 修改（追加扫描步骤） |
| `scripts/make_artifacts.py` | 修改：① check_artifacts 增加 VERSION 一致性校验（~5 行）；② build_marketplace 保留既有 source 仅更新 version（~2 行——D6 决策 A 配套，防 --build 把 source 打回相对路径） |
| `skills/devorder-guide/src/package_skill.py` | 修改：excluded 集合补 `"docs"`（v1.1 遗留防御补丁——实测真源当前无 docs/，实际无害，防御性固化） |

### 3.4 预期结果

`bash scripts/release.sh 0.7.0` 一条命令八步：bump（含 frontmatter 迁移）→ 七连全绿 → build + **双形态打包（platform-pack）** → 敏感零命中 → 五方一致（+平台人工确认）→ 双推 → release.yml 自动出 Release 附 `.skill` + `SHA256SUMS`；平台侧 `-upload.zip` 就绪。

### 3.5 潜在风险及应对

| 风险 | 概率 | 应对 |
|---|---|---|
| bump 正则匹配失败（SKILL.md frontmatter 嵌套缩进） | 低 | release_helpers.py 用 `re.M|re.S` 多行模式匹配 `metadata:` 块；首跑前单测正则（`python -c` 冒烟） |
| 五方核对含生成物（plugin.json）→ 顺序错误必红 | 低 | release.sh [3/8] build 先于 [6/8] verify（顺序已固化）；CI 上 make_artifacts --check 的 plugin 副本校验「若存在才查」（既有降级模式，CI 无 plugins/ 不误杀） |
| 敏感词表生成脚本留在内部仓 → 词表更新流程断裂 | 中 | 文档写明：改词表 → 内部跑 gen_lexicon.py → 更新 .enc → 提交公开仓（配套纪律段） |
| release.yml 扫描失败阻塞 Release | 低 | 这正是 fail-closed 设计意图；修复后重打 tag 触发 |
| GitCode push 失败 | 中 | 不阻断（脚本已容错）；补推命令记录到 SOP |

### 3.6 验收清单

- [ ] `bash scripts/release.sh 0.7.0-rc1`（试发布版）全 8 步通过
- [ ] bump 顺序核对：[1/8] bump（含 frontmatter 幂等迁移）→ [2/8] 七连（七连验证的是发布态）
- [ ] **frontmatter 迁移核对**：bump 后 `grep -E '^version:|^identity:' skills/devorder-guide/SKILL.md` 输出 `version: "0.7.0-rc1"` + `identity: CUSTOMER`（约定 §2/§3 形态）；`metadata.version` 不再存在
- [ ] 五方核对输出 `pyproject=0.7.0-rc1 SKILL.md=0.7.0-rc1 plugin=0.7.0-rc1 marketplace=0.7.0-rc1 VERSION=0.7.0-rc1` + verify 末尾「⚠️ 平台上传版本须人工确认」（六方口径）
- [ ] **敏感注入实验**：dist 内放含敏感词的长句文本文件 → 扫描 exit 1 拦截（词级命中验证，v1.1 P0 全量匹配核心点）
- [ ] **双形态打包实验（v2.2）**：`platform-pack` 后 `unzip -l dist/devorder-guide-v0.7.0-rc1-upload.zip` 首项为 `devorder-guide/SKILL.md`（外层目录形态，约定 §1）；扁平 `devorder-guide.skill` 仍为 SKILL.md 在根（update.py 兼容）
- [ ] release.yml 扫描步骤在 `--check --tag` 之前执行
- [ ] `VERSION` 与 `make_artifacts --check` 联动（改 VERSION 后 --check 必红，grep 验证后还原）
- [ ] `git push origin main --tags` + `git push gitcode main --tags` 双推成功
- [ ] GitHub Release 页出现 v0.7.0-rc1 + `.skill` + `SHA256SUMS` 资产
- [ ] GitCode 镜像 v0.7.0-rc1 tag 可见
- [ ] 敏感词表明文/生成脚本不在 `git ls-files` 中

---

## 四、S3 阶段：SKILL.md 更新段 + 用户文档

### 4.1 目标

用户在任何宿主一句话即可触发版本检查；安装文档完整覆盖三渠道的更新机制。

### 4.2 具体操作

**步骤 1：SKILL.md 末尾追加「版本检查与更新」段（正文末尾，~22 行；v2.1 扩展为双段，对齐约定 §6/§7 的 Harness 自动更新最小示例）**

> v2.1 说明：SKILL.md 更新段同时承担两职责——① **平台线**：按约定 §6/§7 告诉 Harness「本地版本 / identity / 查询接口 / downloadUrl 下载 / 校验 / 替换 / 重载」（平台 Harness 自动执行）；② **开源线**：一句话触发 `update.py`（GitHub/GitCode 源）。两段版本号各自独立，互不混比。

```markdown
## 版本检查与更新

### 平台自动更新（Harness 按约定执行）

- 当前版本：`0.7.0`（与 SKILL.md frontmatter `version` 一致）
- 适用身份：`CUSTOMER`
- 版本查询接口：`GET /api/v1/skills/version?identity=CUSTOMER&currentVersion=0.7.0`
- 下载接口：使用版本查询响应中的 `downloadUrl`（**不要根据版本号自行拼接下载地址**——约定 §5）

Harness 启动时或按更新策略调用版本查询接口：
- `latestVersion` 与 `0.7.0` 相同 → 继续使用当前 Skill。
- `latestVersion` 与 `0.7.0` 不同 → 读取 `downloadUrl` 下载新 Skill 包。
- 下载完成后校验新包内 `SKILL.md` 的 `version` == `latestVersion`；校验通过后替换本地旧版本并重新加载。
- `forceUpdate` 为预留字段：若返回 `true`，优先完成更新再继续依赖本技能的任务。
- 更新时先写临时目录、完成下载和校验后再替换，避免网络中断导致本地技能不完整（约定 §6）。

### 一句话触发检查（公开仓开源线）

用户说「检查 devorder-guide 更新 / 有没有新版 / 更新本技能」时：
1. 执行 `python <技能目录>/scripts/update.py --check`（只读，无副作用；约 1~3 秒；检测源：GitHub API 主源 + GitCode 镜像降级）
2. 有新版时向用户报告「本地 vX.Y.Z → 远端 vA.B.C（检测源：GitHub / 镜像）」，并说明两种更新方式：
   - 一键更新：用户明确同意后执行 `python <技能目录>/scripts/update.py --yes`
     （写操作：下载 → SHA256 校验 → 解压 → 原子替换；失败自动回滚，旧版保留于 .bak-*）
   - 手动更新：从 GitHub Release 页下载 `devorder-guide.skill` 覆盖安装
3. 网络不可用时如实告知「检查失败，当前版本 vX.Y.Z 功能不受影响」，可稍后重试
4. 更新完成后提示用户重启会话或重新加载技能使新版本生效
```

> ⚠️ 纪律：① 追加后**必跑 hit_check 回归**（预期零漂移，但须实测：`python skills/devorder-guide/scripts/hit_check.py` 输出 23·23·0·10）；② 「引导」二字零出现（`grep -c "引导" skills/devorder-guide/SKILL.md` = 0）；③ **frontmatter 约定化由 S2 bump 幂等迁移保证**（顶层 `version` + `identity: CUSTOMER`，v0.7.0 起），正文追加不得改动其他 frontmatter 字段；④ 平台线接口 URL 为占位示例——以实际部署地址为准，**不得硬编码具体版本下载地址**（约定 §5）。

**步骤 2：INSTALL.md 追加「更新机制」章节（放在通道表之后）**

```markdown
## 更新机制（装完怎么拿新版）

| 工具 | 更新方式 | 档位 |
|---|---|---|
| Claude Code | 开启 autoUpdate 后完全自动：/plugin → Marketplaces → devorder-guide → Enable auto-update（一次性）；之后每次启动后台拉新版，按提示 /reload-plugins 生效 | T1 全自动 |
| Codex / Cursor / 其他 CLI | `gh skill update devorder-guide`（GitHub CLI ≥ 2.90） | T2 半自动 |
| WorkBuddy | 对 AI 说「检查 devorder-guide 更新」→ 技能自带 update.py 完成检查/更新 | T2 半自动 |
| InsCode | 下载最新 Release 的 `devorder-guide.skill` 手动重导（平台暂无原生更新机制） | T3 手动 |

> ⚠️ 从 v0.7.0 起技能包内含 update.py；更早版本（如 v0.5.29）需手动升级一次到 v0.7.0 后才能享受版本检查。
```

**步骤 3：README.md 追加「更新方式」段（客户入口）**

```markdown
## 🔄 更新方式

- **Claude Code**：开启 autoUpdate 后自动更新（安装时按提示开启即可）
- **Codex/Cursor 等 CLI**：`gh skill update devorder-guide`
- **WorkBuddy**：对 AI 说「检查 devorder-guide 更新」
- **任何环境**：`python <技能目录>/scripts/update.py --check`（只读检查）
- 全部渠道以 GitHub Release 为唯一权威源（tag = 版本）；国内网络自动走 GitCode 镜像
```

### 4.3 涉及文件

| 文件 | 动作 |
|---|---|
| `skills/devorder-guide/SKILL.md` | 末尾追加更新段（双段：平台线约定接口 + 开源线 update.py）；frontmatter 约定化由 S2 bump 幂等迁移完成，S3 不单独处理 |
| `INSTALL.md` | 追加更新机制章节 |
| `README.md` | 追加更新方式段 |

### 4.4 预期结果

- SKILL.md 更新段（双段）就位，hit_check 零回归，「引导」= 0，frontmatter 已为顶层 `version` + `identity: CUSTOMER`
- INSTALL.md 四行更新表覆盖全部渠道

### 4.5 潜在风险及应对

| 风险 | 概率 | 应对 |
|---|---|---|
| hit_check 出现回归 | 低 | 追加段在正文末尾且不动 description/whenToUse；若有漂移按 hit_check 报告调整措辞 |
| 文档泄漏内部术语/渠道名 | 低 | 文档写完过一遍 sensitive_scan_repo.py（S2 词表） |
| 平台线接口 URL 为占位（example.com）→ 部署后 SKILL.md 与实际不符 | 中 | 平台接口地址定稿后同步更新 SKILL.md 更新段（版本化发布，走 release.sh）；公开仓线不受影响 |
| frontmatter 迁移破坏描述字段或 YAML 解析 | 低 | bump 幂等迁移只动 version/identity 两处；S2 验收「frontmatter 迁移核对」+ hit_check 兜底 |

### 4.6 验收清单

- [ ] `python skills/devorder-guide/scripts/hit_check.py` 输出 23·23·0·10 零漂移（追加段 + frontmatter 迁移后）
- [ ] `grep -c "引导" skills/devorder-guide/SKILL.md` = 0
- [ ] `grep -E '^version:|^identity:' skills/devorder-guide/SKILL.md` 含顶层 `version` + `identity: CUSTOMER`（约定 §2/§3）
- [ ] SKILL.md 更新段含双段：平台线（identity/查询接口/downloadUrl/校验/重载）+ 开源线（update.py 一句话触发）
- [ ] INSTALL.md 更新机制表三渠道命令逐条可执行
- [ ] README 更新方式段就位
- [ ] `bash skills/devorder-guide/scripts/check_all.sh` 全绿（S3 后最终回归）

---

## 五、S4 阶段：双原生渠道真机验证

### 5.1 目标

在真实第三方环境验证三条更新链路 + 一条探针，产出实测报告。**本阶段所有结论以真机为准，不预设通过**。本机环境已核实齐备：Claude Code 2.1.169 / gh 2.96.0 / Python 3.14.3 / WorkBuddy 客户端（已装 v0.5.29 旧版）。

### 5.2 具体操作

**前置：试发布 v0.7.0-rc1（S2 验收产物）**——所有链路以 rc1 为安装基线，正式 v0.7.0 为更新目标。

**链路 1：Claude Code 插件市场（T1 全自动，原生渠道①）**

```bash
# 1. 添加市场 + 安装（D6 决策 A 时 source 指向 Release zip）
claude
/plugin marketplace add YangShen71/devorder-guide
/plugin install devorder-guide@devorder-guide-marketplace
# 2. 验证技能加载：新会话问「你能看到 devorder-guide 技能吗」
# 3. 开启自动更新：/plugin → Marketplaces → devorder-guide → Enable auto-update
# 4. 更新实验：发布正式 v0.7.0 后 → 新会话 → 等待 ≤10 分钟随机延迟
#    → 观察更新通知 → /reload-plugins → 验证 SKILL.md version == 0.7.0
ls ~/.claude/plugins/cache/   # 记录插件缓存目录 mtime
```

**链路 2：gh skill → Codex（T2 半自动，原生渠道②）**

```bash
gh skill --help                # ✅ 已实测（2026-08-23）：2.96.0 含 install/list/preview/publish/search/update 六子命令；--agent 支持 codebuddy
gh skill install YangShen71/devorder-guide devorder-guide --agent codex --scope user
ls ~/.agents/skills/devorder-guide/SKILL.md
head -5 ~/.agents/skills/devorder-guide/SKILL.md   # 应见 gh-skill-source/ref 溯源元数据
# 更新实验：发布 v0.7.0 后
gh skill update devorder-guide
grep version ~/.agents/skills/devorder-guide/SKILL.md   # 期望 0.7.0
```

**链路 3：WorkBuddy 一句话触发 update.py（T2，全平台版本检查主战场）**

```bash
# ① 手动安装 v0.7.0-rc1 包到 WorkBuddy（旧 v0.5.29 包内无 update.py，首次必须手动）
mkdir -p ~/.workbuddy/skills/devorder-guide
unzip -o ~/Downloads/devorder-guide-v0.7.0-rc1.skill -d ~/.workbuddy/skills/devorder-guide/   # 或 Release zip
python ~/.workbuddy/skills/devorder-guide/scripts/update.py --check   # 直测：报「本地 0.7.0-rc1 / 远端 0.7.0-rc1」
# ② 一句话触发实测：对 WorkBuddy AI 说「检查 devorder-guide 更新」
#    → AI 执行 --check（截图留证：AI 确实执行了脚本并汇报）
# ③ 更新实验：发布正式 v0.7.0 后再次触发 → AI 执行 --yes（用户同意后）
#    → SKILL.md version == 0.7.0 + .bak-0.7.0-rc1-* 存在
```

**链路 4：codebuddy 路径探针（关键未知项，gh skill 是否原生覆盖 WorkBuddy）**

```bash
gh skill install YangShen71/devorder-guide devorder-guide --agent codebuddy --scope user
# 安装后立即查三个候选路径：
ls -d ~/.workbuddy/skills/devorder-guide 2>/dev/null && echo "命中 workbuddy"
ls -d ~/.codebuddy/skills/devorder-guide 2>/dev/null && echo "命中 codebuddy"
ls -d ./.claude/skills/devorder-guide 2>/dev/null && echo "命中 claude"
# 结论三分支：
# ① 命中 ~/.workbuddy/skills/ → WorkBuddy 升级为 gh skill 原生渠道（update.py 降为兜底）
# ② 命中其他路径 → update.py 仍为主方案，记录路径关系
# ③ 报错 → 记录实测结果，update.py 为主方案
```

**附加：marketplace source 终审（G1 修复验证）**

D6 决策 A 时：`/plugin install` 成功即终审通过；失败则按报错切换 B/C，**以真机报错为唯一权威**，修正后重走 release.sh 0.7.0-rc2。

### 5.3 涉及文件

| 项 | 说明 |
|---|---|
| `docs/review/hot-update-live-test-20260823.md` | 新建：四链路实测报告（命令输出 + 截图 + 时间戳证据） |
| `~/.claude/settings.json` | 用户侧 autoUpdate 配置（实验用，实验后还原） |
| `~/.agents/skills/`、`~/.workbuddy/skills/` | 真机目标目录 |

### 5.4 预期结果

- 链路 1：市场安装成功 + autoUpdate 将 v0.7.0 拉取到 `~/.claude/plugins/cache/`（时间戳证据）
- 链路 2：install 注入溯源元数据 + update 拉新成功（0.7.0-rc1 → 0.7.0）
- 链路 3：WorkBuddy AI 一句话触发 `--check` 实锤 + `--yes` 一键更新成功（0.7.0-rc1 → 0.7.0）
- 链路 4：codebuddy 路径结论明确（三分支之一）
- G1 终审：marketplace source 方案定稿

### 5.5 潜在风险及应对

| 风险 | 概率 | 应对 |
|---|---|---|
| `/plugin marketplace add` 或 install schema 报错 | 中 | 按报错逐字段修正（G1 已预警）；修正后重发布 rc2；记录最终 schema 形态供 S5 归档 |
| autoUpdate 未生效（第三方市场默认关/延迟>10min） | 中 | 确认用户级 settings autoUpdate: true；检查 cache mtime；超时重试一次，记录实测延迟 |
| gh skill preview 语义演进（子命令行为变化） | 低（2.96.0 六子命令已实测：install/list/preview/publish/search/update） | 发布声明以当日 `gh skill --help` 为准；update.py 不依赖 gh CLI（urllib 直连）兜底 |
| WorkBuddy AI 不执行 --check（遵循度问题） | 中 | 换措辞多次尝试；仍失败记录为「AI 遵循度限制」，报告如实标注 |
| 本机测试污染生产环境（cache/目录被改） | 低 | 实验前记录各目录原状；实验后还原（或保留新版本——本身是目标） |

### 5.6 验收清单

- [ ] 链路 1：`/plugin install` 成功 + 新会话技能可触发 + autoUpdate 拉新（cache mtime 证据 + version == 0.7.0）
- [ ] 链路 2：`~/.agents/skills/devorder-guide/SKILL.md` 含溯源元数据 + `gh skill update` 后版本 0.7.0-rc1 → 0.7.0
- [ ] 链路 3：WorkBuddy AI 实际执行了 `--check`（截图留证）+ `--yes` 更新成功 + `.bak-*` 存在
- [ ] 链路 4：codebuddy 探针三分支结论明确
- [ ] G1 终审结论明确（A/B/C 定稿）
- [ ] 实测报告落盘 `docs/review/hot-update-live-test-20260823.md`（含全部证据）

---

## 六、S5 阶段：v0.7.0 发布与验收

### 6.1 目标

正式发布 v0.7.0，全量验收清单 100% 打勾归档；可选完成 `gh skill publish` 供应链加固。

### 6.2 具体操作

**步骤 1：正式发布**

```bash
cd /c/Users/阳神71/Desktop/devorder-guide
bash scripts/release.sh 0.7.0    # S4 全部验收通过后执行
```

**步骤 2：可选增强——`gh skill publish` + immutable releases（供应链加固）**

```bash
gh skill publish --dry-run   # 校验 agentskills.io 规范 + 远端安全配置建议（✅ publish 子命令已实测存在于 2.96.0）
gh skill publish             # 按提示开启 immutable releases（历史版本内容不可篡改）
```

**步骤 3：验收报告归档**

- `docs/review/release-v0.7.0-acceptance.md`：本文档第十章全部清单 + S0~S5 各阶段验收项的汇总表
- 实测支持矩阵更新：README/DEV.md 的「已实测支持表」以 S4 报告为证（实测背书红线）

**步骤 4：发布前检查（对齐 `skill-package-generation-guide.md` §8 十项，v2.1 新增）**

> 约定 §8 要求「上传运营端前至少检查」10 项。公开仓 GitHub 分发不经运营端上传，但**若同一包上架平台线**（运营端上传），本表逐项对照落地；公开仓分发侧对应项也一并标注。S5 验收时逐项打勾归档进验收报告。

| # | 约定 §8 检查项 | 公开仓侧落地 | 平台线上架落地 | 对应方案章节 |
|---|---|---|---|---|
| 1 | 压缩包可以正常解压 | `unzip -l dist/*.skill` + verify_install.sh 解压验证 | 同左 | S1/S2 |
| 2 | `SKILL.md` 位于约定目录 | **扁平形态**（`SKILL.md` 在 zip 根）——公开仓自消费（update.py/Claude/gh skill）；⚠️ v2.2 实证：dist 即此形态，**不可直接上架平台** | **外层目录形态**（`devorder-guide/SKILL.md`，约定 §1「压缩包根目录下的 Skill 目录中」）——必须用 `platform-pack` 产出的 `-upload.zip`（G7/D9） | S2 双形态打包 |
| 3 | `name`/`version`/`identity` 字段存在且格式正确 | bump 幂等迁移保证顶层 `version` + `identity: CUSTOMER`（v2.1） | 同左（上传前 grep 三字段） | S2 验收 |
| 4 | `SKILL.md` 内版本号与运营端填写的版本号一致 | 五方核对（不含平台） | **人工确认**上传表单版本 == frontmatter version（约定 §3.99） | 7.1/verify 六方口径 |
| 5 | `identity` 与运营端选择的身份一致 | frontmatter `identity: CUSTOMER` | 上传时身份选 CUSTOMER | 7.1 |
| 6 | 版本查询接口中的 `identity` 与 Skill 身份一致 | —（开源线不经平台接口） | SKILL.md 更新段写 `identity=CUSTOMER` | S3 步骤 1 |
| 7 | 使用 `/api/v1/skills/version` 版本查询接口 | — | SKILL.md 更新段平台段使用该接口 | S3 步骤 1 |
| 8 | 更新时使用服务端返回的 `downloadUrl`，没有硬编码版本下载地址 | update.py 从 GitHub API 响应取 assets URL（等价纪律） | SKILL.md 平台段明示「不得硬编码」 | S1/S3 |
| 9 | 包内没有 API Key/JWT/密码或其他生产凭据 | 敏感扫描 fail-closed + 双保险 | 同左（上架前跑一遍 sensitive_scan_repo.py） | S2/九 R1 |
| 10 | Skill 未声明不存在的工具或接口 | 契约审计（check_all 七连含） | 同左 | S2 |

### 6.3 涉及文件

`docs/review/release-v0.7.0-acceptance.md`（新建，含步骤 4 发布前检查十项对照表）；README/DEV.md（实测矩阵更新）。

### 6.4 潜在风险及应对

| 风险 | 概率 | 应对 |
|---|---|---|
| 首发后发现 S4 实测遗漏问题 | 低 | 首发前 S4 清单 100% 打勾为硬前置；问题走 v0.7.1 补丁（PATCH，tag 链可回退） |
| gh skill publish 报规范错误 | 中 | 按报错修正（多为 frontmatter 字段）；不阻塞 v0.7.0 发布 |

### 6.5 验收清单

- [ ] `bash scripts/release.sh 0.7.0` 八步全绿 + Release 附 `.skill` + `SHA256SUMS`
- [ ] GitCode 镜像 v0.7.0 同步
- [ ] 三渠道更新生效复核（S4 之后 autoUpdate / gh skill update / update.py --check 均报 0.7.0）
- [ ] `gh skill publish --dry-run` 结果记录（零报错或未通过项 + 原因）
- [ ] **发布前检查十项对照表（约定 §8）逐项打勾**（v2.1 步骤 4）
- [ ] 验收报告落盘（全部清单归档）

---

## 七、版本号管理与发布流程规范（长效纪律）

### 7.1 版本五方一致性 + 平台六方口径（约定 §3 对齐，v2.1）

版本真源 = `skills/devorder-guide/pyproject.toml`；以下四处必须与其相等，release.sh [6/8] 硬校验（五方）：

1. `skills/devorder-guide/SKILL.md` → **顶层 `version`**（v2.1 起约定 §3 形态；`metadata.version` 为 v0.6.1 过渡兜底，v0.9.0 移除）
2. `plugins/devorder-guide/.claude-plugin/plugin.json` → `version`（生成物）
3. `.claude-plugin/marketplace.json` → `plugins[0].version`（入库文件）
4. `VERSION`（仓库根，GitCode 降级源）

**平台第六方（人工确认，非脚本硬校验）**：运营端上传表单版本号 == 五方（约定 §3.99：运营端不自动读包内 version，须人工核对；`identity + version` 不允许重复上传）。verify 子命令末尾输出「⚠️ 平台上传版本须人工确认」提示。

**frontmatter 形态纪律（v2.1 新增）**：
- `SKILL.md` frontmatter 必须含顶层 `version` + `identity: CUSTOMER`（约定 §2/§3）；禁止回退到 `metadata.version` 嵌套形态
- `identity` 与运营端上传时选择的身份一致（CUSTOMER）
- 同一身份下平台只保留一个 `ACTIVE` 版本——上传新版后旧版自动 `DISABLED`（约定 §2）

CI 侧：`make_artifacts.py --check`（含新增 VERSION 校验）+ `--check --tag`（release.yml）双守卫；`verify_install.sh` 的插件核对保持 v1.1 的「存在才查、缺失 warn」降级模式（CI runner 无 plugins/ 不误杀）。

### 7.2 版本语义（语义化版本，约定 §3）

| 变更类型 | 版本动作 | 示例 |
|---|---|---|
| 文案修正/注释/文档 | PATCH +0.0.1 | v0.7.0 → v0.7.1 |
| 新增兼容能力（update.py 进化/新品类/新工具） | MINOR +0.1.0 | v0.7.0 → v0.8.0 |
| 结构破坏性变更（工具名称/调用方式/角色边界不兼容） | MAJOR | v1.0.0（首发冻结，S4/S5 验收通过后决策） |

版本号三处一致要求（约定 §3）：`SKILL.md version` = 运营端上传表单 = Harness `currentVersion`。公开仓 GitHub tag 为开源线版本权威（tag = 版本，immutable releases 可选加固）。

### 7.3 发布 SOP（每次发版固定流程）

```
开发完成 → bash scripts/release.sh <ver>
  ├─ [1/8] bump（SKILL.md + pyproject + VERSION；含 frontmatter 幂等迁移为顶层 version + identity——先 bump，七连验证发布态）
  ├─ [2/8] check_all 七连 + pytest 单测（失败即止）
  ├─ [3/8] make_artifacts --build（dist + 插件副本 + 双 marketplace + 镜像）
  ├─ [4/8] 敏感扫描（fail-closed，XOR 词表全量匹配）
  ├─ [5/8] marketplace source 版本化（D6 A；决策 B/C 时注释该行）
  ├─ [6/8] 五方核对（硬校验）+ make_artifacts --check --tag + 平台上传版本人工确认（六方口径）
  ├─ [7/8] commit + tag + 双推（GitHub 权威 + GitCode 镜像）
  └─ [8/8] release.yml 自动出 Release（.skill + SHA256SUMS）
           → Claude autoUpdate（≤10min）/ gh skill update / update.py 三渠道生效
```

### 7.4 GitCode 镜像同步纪律

- 每次发布双推（release.sh [7/8] 固化）；GitCode push 失败不阻断 GitHub 发布，但**补推**列入 SOP（`git push gitcode main --tags`）
- VERSION 文件依赖镜像同步——镜像滞后期间 update.py 降级源可能报旧版本，属可接受（主源 GitHub 优先，降级只兜底）
- 可选二期：release.yml 增加镜像 job（需 GITCODE_TOKEN secret，配置后再加）

### 7.5 敏感词表维护纪律

改词表流程：内部 `devorder-guide-workspace/v0.4-audit/gen_lexicon.py`（永不入库）→ 重新生成 `.enc` → 提交公开仓 → release.sh [4/8] + release.yml 立即生效。

### 7.6 包结构与分发纪律（v2.2，对齐约定 §1）

- **双形态打包（G7/D9）**：公开仓 Release 只发布扁平 `devorder-guide.skill`（update.py/Claude 插件/gh skill 消费）；平台线上架必须用 `platform-pack` 产出的 `devorder-guide-v{ver}-upload.zip`（外层目录 `devorder-guide/SKILL.md`，约定 §1「SKILL.md 必须位于压缩包根目录下的 Skill 目录中」）；**扁平包永不直传运营端**
- `-upload.zip` 为生成物不入库；如需要可手动附到 GitHub Release（不自动附，避免与 .skill 混淆）
- **工具 schema 不固化（约定 §1）**：SKILL.md/参考文档不得固化 DevOrder MCP 工具的参数 schema——工具参数以当前 MCP Server 返回的 schema 为准；`allowed-tools` 只列工具名（白名单），不列参数结构
- **凭据零入包（约定 §1）**：包内禁止 API Key/JWT/密码等生产凭据——sensitive_scan 词表含凭据类模式，fail-closed 兜底

---

## 八、深度优化标准（可量化指标）

| 指标 | 目标值 | 测量方法 |
|---|---|---|
| **更新成功率** | 三渠道各 1/1（0.7.0-rc1 → 0.7.0 全链路） | S4 三链路实测（autoUpdate 含 ≤10min 延迟等待，全链路约 40 分钟） |
| **检查耗时** | `update.py --check` ≤ 5s（含双源超时上限 20s 外的正常路径） | S4 计时（`time python ... --check`） |
| **安装耗时** | `/plugin install` ≤ 30s；`gh skill install` ≤ 15s；`--yes` ≤ 20s | S4 各取 3 次中位数 |
| **版本一致性** | 五方核对零差异率 100% | release.sh [6/8] 每次强制 + make_artifacts --check（CI） |
| **渠道覆盖完整性** | Claude ✅ / Codex ✅ / WorkBuddy ✅ / InsCode ⚠️手动（3.5/4） | S4 实测矩阵 |
| **敏感零泄漏** | 词表命中数 = 0（100%） | release.sh [4/8] + release.yml CI 双保险 |
| **回退可靠性** | 60s 内可回退（git reset / --rollback / @tag 重装） | S4 各演练 1 次 |
| **断网降级** | 全渠道断网技能可用性 100%（更新失败不影响运行） | S1 断网实验 + S4 复核 |
| **hit_check 回归** | SKILL.md 任何变更后 23·23·0·10 零漂移 | 每次涉及 SKILL.md 的发布 |

---

## 九、风险与应对汇总（跨阶段）

| # | 风险 | 等级 | 应对 | 责任阶段 |
|---|---|---|---|---|
| R1 | 敏感信息误入公开仓（未来误提交） | 🔴 | XOR 混淆词表 fail-closed 全量扫描 + release.yml CI 双保险 + 发布前人工抽查 | S2 |
| R2 | gh skill public preview 语义变更（子命令行为演进） | 🟠（update/publish 存在性已实测确认，风险降至行为变化） | 以 `gh skill --help` 实列为准；update.py 不依赖 gh CLI（urllib 直连） | S4 |
| R3 | Claude Code 第三方市场 autoUpdate 默认关 | 🟠 | INSTALL.md/README 显式指引开启；README 更新机制段明示 | S3 |
| R4 | 国内网络对 github.com 可达性 | 🟠 | GitCode 镜像双源（--check 降级 raw VERSION）；如实告知下载受限场景 | S0/S1 |
| R5 | update.py 供应链攻击面 | 🟠 | --yes 显式确认门禁 + **SHA256SUMS 资产校验**（v2.0 增强）+ 版本/关键文件校验 + 失败自动回滚 | S1 |
| R6 | AI 主动执行 --check 遵循度不稳定 | 🟡 | SKILL.md 确定性指令措辞 + 用户显式触发为主入口 | S3 |
| R7 | plugin/marketplace schema 演进（含 G1 source 缺口） | 🟡 | S4 真机报错驱动修正；D6 三选项备好回退 | S0/S4 |
| R8 | GitCode 镜像不同步 → VERSION 降级源失效 | 🟡 | 发布 SOP 双推固化 + 补推命令记录；镜像滞后仅影响降级路径 | S2/7.4 |
| R9 | 自举悖论：旧版（v0.5.29）无 update.py | 🟡 | 诚实披露 + INSTALL.md 明示「首次需手动升级」；S4 实证 | S3/S4 |
| R10 | release.sh 误操作（bump 错版本/推错分支） | 🟡 | [6/8] 五方硬校验 + `--check --tag` 双守卫 + set -euo pipefail | S2 |
| R11 | 词表生成脚本留在内部仓 → 词表更新断裂 | 🟡 | 7.5 维护纪律文档化 | S2/7.5 |
| R12 | **frontmatter 迁移破坏旧解析**（v0.6.1 用户/旧脚本依赖 `metadata.version` 形态） | 🟡 | 双模式解析兜底保留至 v0.9.0（update.py/release_helpers/verify 同构）；S1 双形态单测 + S2 迁移验收 | S1/S2 |
| R13 | **平台/开源版本线混淆**（平台 1.x 与公开仓 0.x 误比 → 误报更新或误跳过） | 🟡 | 双轨制明文：update.py 只查 GitHub/GitCode（0.x）；平台线由 SKILL.md 约定接口承载（1.x）；SKILL.md 更新段两段独立标注版本号 | S1/S3/7.1 |
| R14 | **包结构形态混淆致平台上架失败**（v2.2：扁平 .skill 直传运营端 → 不合规/解析异常） | 🟡 | 双形态打包纪律（7.6）：平台侧只用 platform-pack 产出的 -upload.zip；S2 双形态验收（unzip -l 核对首项路径） | S2/7.6 |

---

## 十、总验收清单（S0~S5 汇总，v0.7.0 发布前 100% 打勾）

**基建（S0）**
- [ ] 基线报告 `docs/review/state-baseline-20260823.md` 落盘（含 G1~G5 证据）
- [ ] D6 决策明确；GitCode remote 配置 + 首次双推成功
- [ ] VERSION 文件 = 0.6.1；GitCode raw 预检通过

**版本检查（S1）**
- [ ] update.py --check/--yes/--rollback 全路径实测（含断网/篡改/坏包/Zip Slip/只读 5 类注入实验）
- [ ] 版本比较单测（0.10.0 > 0.9.0）通过；pytest 总数 5 → 8 全绿

**管线（S2）**
- [ ] release.sh 0.7.0-rc1 试发布 8 步全绿（bump 在七连前）
- [ ] 五方核对零差异；敏感注入实验拦截；release.yml 扫描门禁生效
- [ ] **双形态打包验收（v2.2）**：`-upload.zip` 首项 `devorder-guide/SKILL.md`（约定 §1）；扁平 `.skill` SKILL.md 在根（update.py 兼容）
- [ ] GitHub + GitCode 双推成功；Release 附 .skill + SHA256SUMS

**文档（S3）**
- [ ] SKILL.md 更新段（双段：平台线约定接口 + 开源线 update.py）就位；hit_check 23·23·0·10 零回归；「引导」= 0
- [ ] frontmatter 已迁移：顶层 `version` + `identity: CUSTOMER`（约定 §2/§3）；`metadata.version` 不再存在（v2.1）
- [ ] INSTALL.md 更新机制表 + README 更新方式段就位

**真机验证（S4）**
- [ ] Claude Code 市场安装 + autoUpdate 拉新（证据：cache mtime + version）
- [ ] gh skill install/update 实测 + 溯源元数据确认
- [ ] WorkBuddy AI 一句话触发 --check/--yes（截图留证）
- [ ] codebuddy 探针结论明确；G1 终审定稿
- [ ] 实测报告 `docs/review/hot-update-live-test-20260823.md` 落盘

**发布（S5）**
- [ ] `bash scripts/release.sh 0.7.0` 全绿；三渠道更新生效复核
- [ ] gh skill publish --dry-run 结果记录（可选步骤）
- [ ] **发布前检查十项对照表（约定 §8）逐项打勾**（v2.1 步骤 4）
- [ ] 验收报告 `docs/review/release-v0.7.0-acceptance.md` 落盘（本文档全部清单归档）

---

## 附 A：决策点（待阳神确认或已决策）

| # | 决策点 | 状态/建议 | 影响 |
|---|---|---|---|
| D1 | 公开仓 license（Proprietary） | **已定**（v0.6.0 发布沿用） | — |
| D2 | owner/仓库名 | **已定**：YangShen71/devorder-guide（GitHub + GitCode 双端） | — |
| D3 | dist 是否含 docs/ | **已关**（实测真源无 docs/ 目录，dist 天然不含 docs）；⚠️ v2.0 复审更正：excluded 实无 "docs"（v1.1「已固化」不实），防御补丁列为 S2 动作 | — |
| D4 | GitCode 镜像 | **已定稿启用**（c83bb7b）；本期补 remote + 双推 + 降级源 | S0 |
| D5 | 私有仓 push 策略 | **已失效**（v2.0 单仓化，无私有仓推云动作） | — |
| **D6** | **marketplace source 缺口修复**（G1，新增）：A. 指向 GitHub Release zip（推荐）/ B. plugins/ 入库 / C. 仓库根 plugin.json + source "./" | S0 决策、S4 真机终审；**以真机报错为唯一权威** | S0/S4 |
| **D7** | GitCode 资产下载降级（--yes 时 GitHub 不可达的下载兜底：GitCode release 资产或 archive） | **二期增强**，本期 --yes 下载失败如实告知手动路径 | S1 后 |
| **D8** | **frontmatter 约定化**（G6，v2.1 新增）：公开仓 SKILL.md 迁移为顶层 `version` + `identity: CUSTOMER`（约定 §2/§3）；`metadata.version` 兜底保留至 v0.9.0 | **已定**（对齐约定强制项，非可选项）；由 release_helpers bump 幂等迁移自动执行，S2 验收核对 | S1/S2/S3 |
| **D9** | **dist 双形态打包**（G7，v2.2 新增）：公开仓 Release 扁平 `.skill`（自消费，现状不变）+ 平台 `-upload.zip` 外层目录形态（约定 §1） | **已定**（实证 dist 扁平形态与约定 §1 冲突）；`platform-pack` 子命令产出，生成物不入库 | S2/7.6 |

## 附 B：v2.0 审查修订记录 + v1.1 保留成果清单

### B1. v2.0 自审修订记录（2026-08-23 产出时自查）

| # | 级别 | 位置 | 缺陷 | 修订 |
|---|---|---|---|---|
| V1 | P0 | 0.3 盘点 | 最初假定 marketplace source 相对路径可工作——实测 `git ls-files plugins` = 0 证明 `source: "./plugins/devorder-guide"` 指向不存在目录，CI 因「若存在才校验」不拦截 | 新增 G1 缺口 + D6 三选项 + S4 终审 |
| V2 | P0 | S1 update.py | v1.1 用 zipball_url 下载无内容校验，供应链加固不足 | 改为 Release 资产 .skill + SHA256SUMS 校验（v1.1 R5 的升级解） |
| V3 | P1 | S1 update.py | `metadata.version` 是嵌套 YAML（`metadata:\n  version:`），v1.1 草案的顶层正则不匹配 | 正则改多行模式 `^metadata:\s*$.*?^\s+version:`；单测 test_local_version 兜底 |
| V4 | P1 | S1 单测 | v1.1 未测 pre-release 后缀（rc 版会崩 int()） | ver_tuple 加前缀截取 + 单测 test_ver_tuple_handles_suffix；S4 用 rc1 试发布版依赖此能力 |
| V5 | P1 | S2 release.sh | v1.1 的 sync 子命令单仓化后无意义；bump 需覆盖 VERSION | release_helpers.py 删 sync、bump 三元组、verify 五方 |
| V6 | P1 | S4 链路 3 | v0.5.29 旧包无 update.py，「一句话触发」无法直接验证 | 验证序改为：先手动装 rc1 → 直测 --check → AI 触发 --check → 发正式版后 --yes；R9 自举悖论诚实披露 |
| V7 | P2 | 7.1 | verify_install 四方核对在单仓下的语义（plugin.json 在生成物中） | 保持 v1.1「存在才查、缺失 warn」降级；硬校验由 release.sh [6/8] 承担 |
| V8 | P2 | 0.2 | v1.1 的 S3/S4 并行标注与新依赖不一致 | S1/S2/S3 两两可并行、S4 硬性串行，重排依赖表 |

### B2. v1.1 关键成果保留清单（v2.0 直接沿用，不重复开发）

1. ✅ 敏感扫描 **XOR+Base64 混淆词表 + 运行时全量子串匹配**（v1.1 P0 修复，零漏检 + 防明文 grep）
2. ✅ update.py **版本比较 tuple(int)**（v1.1 P0 修复，字典序陷阱单测保留）
3. ✅ verify_install.sh **plugin.json 核对「存在才查、缺失 warn」降级模式**（v1.1 P0 修复，CI 兼容）
4. ✅ Zip Slip 防护逻辑（verify_install.sh 既有实现，update.py 移植）
5. ✅ SKILL.md 变更必跑 hit_check + 「引导」文案纪律
6. ✅ dist 展开 = 发布内容（实测真源无 docs/ 目录，dist 天然不含 docs）；⚠️ v2.0 复审发现「package_skill.py excluded 已固化」不实——实测 excluded = {.pytest_cache, __pycache__, dist, .git, .ruff_cache, tests}，**无 docs**；因真源无 docs/ 实际无害，「excluded 补 docs」已列为 S2 防御动作
7. ✅ release.yml 敏感扫描 CI 双保险设计（v2.0 S2 补回 release.yml）

### B3. v1.1 已过时内容（v2.0 删除，留档备查）

S0 双仓库基建（快照仓/完整历史仓 D5）、S1 发布仓骨架搭建、S2 发布仓同步 sync（v1.1 的 release_helpers bump/sync/verify 三子命令版中 sync 删除）、v1.0.0 首发冻结目标（推迟）、gitee 镜像二期（已由 GitCode 替代）。

### B4. v2.0 第二轮严格复审记录（2026-08-23 真机核验，11 项发现）

**核验方式**：读公开仓源码（make_artifacts.py / package_skill.py / check_all.sh / release.yml）、真机命令（`gh skill --help`、curl GitCode raw、curl GitHub API releases/latest、三处旧安装版本 grep）、三处旧安装目录复核。

**发现并修订（按严重度）**

| # | 级别 | 位置 | 缺陷 | 修订 |
|---|---|---|---|---|
| W1 | P0 | S2 release.sh [5/8] | 内嵌 `python -c` 改 marketplace source——与 v1.1「Python 逻辑全部抽离 release_helpers.py」教训自相矛盾（Windows Git Bash 引号嵌套脆弱） | 新增 `market-source <root> <ver>` 子命令，双 marketplace 同步更新；决策 B/C 时注释该行 |
| W2 | P0 | S1 update.py | 替换失败回滚 `shutil.move(bak→ROOT)` 自身失败时技能目录消失（不可恢复）；do_rollback 先删后移同型漏洞 | 三步式原子替换（挪走→移入→失败恢复，恢复也失败则显式告知 .bak 位置）；do_rollback 先挪后移、成功才丢 |
| W3 | P0 | S2 release_helpers verify | `json.loads(read(plugin.json))`——plugins/ 未生成（独立运行 verify）时读空串抛 JSONDecodeError 崩溃 | `json.loads(read(...) or "{}")` 容错（plugin.json 与 marketplace 两处） |
| W4 | P1 | S2 敏感扫描 | release.yml 扫描整个 checkout 会扫到 `.git/` 对象与生成物（二进制压缩数据可能误命中词条 → fail-closed 误杀发布） | 扫描器内置排除清单：`.git/` `dist/` `plugins/` `__pycache__/` `.pytest_cache/` `*.skill` |
| W5 | P1 | 全文 | sensitive_lexicon.enc 路径不一致（0.1 架构图 scripts/ vs S2 configs/） | 统一根 `configs/`（与内部开发侧一致、与真源隔离） |
| W6 | P1 | 附 B2/D3/3.3 | 「package_skill.py excluded 已固化 docs」不实——实测 excluded = {.pytest_cache, __pycache__, dist, .git, .ruff_cache, tests}，无 docs | 附 B2/D3 更正表述（真源实测无 docs/，实际无害）；3.3 补「excluded 加 docs」防御动作 |
| W7 | P1 | S2 release.sh [2/8] | pytest 依赖本地解释器（${PYTHON} 与 check_all 的 managed venv 可能不同） | 失败时显式提示用 `PYTHON=<venv 路径>` 覆盖 |
| W8 | P2 | S4/6.2/九 R2 | gh skill update/publish 存在性原标【推测】——实测 2.96.0 六子命令全在（install/list/preview/publish/search/update），--agent 含 codebuddy | 升级为【一手实测】；R2 风险措辞改为「行为演进」 |
| W9 | P2 | S0 步骤 4 | GitCode raw URL 原为「预检项」——实测 GitHub 风格 `/raw/main/README.md` 返回 200 | 固化为已实测结果；update.py 的 GITCODE_VER 降级 URL 确认可用 |
| W10 | P2 | 0.3 G5 | 三处旧安装版本原「未核」——实测 claude=0.5.26 / agents=0.5.26 / workbuddy=0.5.29（均无 update.py） | 精确化；S4 自举升级基线明确 |
| W11 | P2 | S1 2.6 验收 | 断网实验依赖真实断网——本机 GitHub API 实测可达 | 补注：用临时改 hosts / 断网显式构造不可达场景 |

**排除项（核验通过，无需修订）**

1. GitHub API assets 结构（browser_download_url + .skill/SHA256SUMS 双资产）——实测与 update.py 解析兼容（`line.split()[0]` 按空白分割，兼容 SHA256SUMS 单/双空格）
2. SKILL.md frontmatter 嵌套 `metadata.version`——update.py/release_helpers 正则与实测文件匹配（`grep -m1 version` 输出 `version: "0.6.1"`）⚠️ v2.1 起改为双模式并迁移（见 B5）
3. 七连不含 pytest——前轮已修正；本轮复核 check_all.sh 实测确认（pytest 由 CI/release.sh 单独跑）
4. marketplace.json 双文件（.claude-plugin + .atomcode-plugin 同内容）——market-source 子命令同步更新两处
5. GitCode 仓库存在性（301 重定向）+ raw 200——降级通道已验证可用
6. `docs/review/` 目录存在（github-release-方案评审-20260820.md）——S0/S4/S5 落盘路径可行
7. v1.1 的 verify_install「存在才查」降级模式——公开仓实现与设计一致（读源码复核）
8. `gh skill --agent codebuddy` 命中 ~/.workbuddy/skills/ 的可能性——保持 S4 链路 4 探针设计（子命令存在不等于行为验证，仍需真机实测）

### B5. v2.1 版本更新修订记录（2026-08-24，对齐 `skill-package-generation-guide.md`）

**核验方式**：读约定文件全 8 章；读公开仓真源 frontmatter（`metadata.version: "0.6.1"` 嵌套、无 identity）；读内部 devorder-guide v1.0.0 frontmatter（顶层 `version: 1.0.0` + `identity: CUSTOMER`）；对照内部 v1.0.0 与约定 §7 最小示例。

**发现并修订（按严重度）**

| # | 级别 | 位置 | 缺陷 | 修订 |
|---|---|---|---|---|
| U1 | P0 | 0.3/附 D3 | 公开仓 SKILL.md frontmatter 用嵌套 `metadata.version` 且无 `identity`——与约定 §2（identity 必填）/§3（顶层 version）冲突；内部 v1.0.0 已是顶层形态，两线形态分裂 | 新增 G6 缺口 + D8 决策（已定）；S2 bump 幂等迁移（顶层 version + identity）；metadata.version 兜底至 v0.9.0（R12） |
| U2 | P0 | S1 update.py | `local_version()`/新包校验只认 `metadata.version`——迁移后（顶层形态）将解析失败 | 抽 `skill_version()` 双模式（顶层优先 + metadata 兜底）；新包校验复用；单测补双形态 2 例（test_skill_version_top_level_first / metadata_fallback） |
| U3 | P0 | S2 release_helpers | `bump`/`verify` 的 SKILL.md 正则只认 `metadata.version`；无 identity 写入能力 | bump 幂等迁移（migrate_frontmatter）+ 顶层替换；新增 `migrate` 子命令；verify 的 SKILL.md 复用 skill_version 双模式 |
| U4 | P1 | S3 步骤 1 | 更新段只含 update.py 一句话触发——未承载约定 §6/§7 的 Harness 自动更新指引（identity/查询接口/downloadUrl/校验/重载） | 更新段扩展为双段：平台线（约定 §7 最小示例全形态）+ 开源线（update.py）；纪律 ③ 改「frontmatter 约定化由 bump 迁移」 |
| U5 | P1 | 7.1 | 版本核对五方不含平台上传版本（约定 §3.99 人工确认项） | 六方口径：五方硬核对 + platform-upload 人工确认 warn（verify 输出）；7.1 补 frontmatter 形态纪律与 identity 一致性 |
| U6 | P2 | 6.2/S5 | 发布前检查未对齐约定 §8 十项 | S5 新增步骤 4「发布前检查十项对照表」（公开仓侧 + 平台侧双落地） |
| U7 | P2 | 7.2/九 | 版本语义未引用约定 §3；风险表缺版本线混淆/迁移破坏项 | 7.2 补三处一致要求；九补 R12（迁移破坏旧解析）/R13（平台/开源版本线混淆） |
| U8 | P2 | 头部/0.4/十 | 文档自身无版本更新文件；总览/验收未体现约定对齐 | 新增「★ 版本更新文件（v2.0→v2.1）」章节（变更摘要/版本号/兼容性/弃用迁移/模块变更记录）；0.4 补「约定对齐」行；总验收补 frontmatter 与发布前检查项 |

**排除项（核验通过，无需修订）**

1. `identity` 取值——devorder-guide 面向发单方需求对话，`CUSTOMER` 正确（内部 v1.0.0 已用，约定 §2 支持 CUSTOMER/CONTRACTOR 两值）
2. 平台查询接口为 `/api/v1/skills/version`——公开仓开源线不经平台接口（双轨制），仅 SKILL.md 平台段引用
3. `forceUpdate` 预留字段——SKILL.md 平台段注明语义，update.py 开源线不处理（平台线专属）
4. 版本号三段式——公开仓 0.x 与平台 1.x 各自符合语义化版本，无格式冲突

### B6. v2.2 版本更新修订记录（2026-08-24，包结构双形态，对齐约定 §1）

**核验方式**：zipfile 读 `devorder-guide/dist/devorder-guide.skill` namelist（27 文件、SKILL.md 在 zip 根、无外层目录）；读 `src/package_skill.py` 打包逻辑（`zf.write(p, rel)` 相对路径扁平写入）；对照约定 §1「SKILL.md 必须位于压缩包根目录下的 Skill 目录中」。

**发现并修订（按严重度）**

| # | 级别 | 位置 | 缺陷 | 修订 |
|---|---|---|---|---|
| X1 | P0 | 0.3/附 D9/打包 | dist 为扁平形态（SKILL.md 在 zip 根），与约定 §1 外层目录形态（`skill-name/SKILL.md`）冲突——扁平包直传运营端将不合规 | 新增 G7 缺口 + D9 决策（已定）；`platform-pack` 子命令产出 `-upload.zip` 外层形态；release.sh [3/8] 并入双形态打包 |
| X2 | P1 | S2 release_helpers | 无平台上架包生成能力 | 新增 `platform_pack()`（扁平 → 外层目录重打包，含 Zip Slip 防护 + 形态断言）；main 分支注册 |
| X3 | P1 | S5 步骤 4 | 十项检查表第 2 项「SKILL.md 位于约定目录」口径与 dist 实际形态不符 | 修正为双口径：公开仓侧扁平（自消费）/ 平台侧外层目录（platform-pack 产物）；并注明「扁平包永不直传运营端」 |
| X4 | P2 | 七章 | 缺 §1 工具 schema 不固化/凭据零入包纪律 | 新增 7.6 包结构与分发纪律（双形态 + schema 不固化 + 凭据零入包） |
| X5 | P2 | 九/十 | 风险表与总验收缺包形态混淆项 | 九补 R14；十 S2 段补双形态验收（unzip -l 首项核对） |

**排除项（核验通过，无需修订）**

1. update.py 解压逻辑与扁平形态自洽（`extract / "SKILL.md"` 直接命中）——扁平形态正是 update.py 的消费前提，双形态不影响
2. Claude Code 插件 / gh skill 对包内目录层级不敏感（读 frontmatter 内容而非目录深度）——扁平形态兼容（S4 真机终审）
3. `.skill` 与 `.zip` 扩展名——扁平包保持 `.skill`（公开仓惯例）；平台上传包用 `.zip`（运营端支持 .zip/.tar.gz，约定 §1）
