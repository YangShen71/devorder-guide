# devorder-guide 开发与发布手册（DEV.md）

## 目录结构

```
devorder-guide/                          # GitHub 公开仓库
├── README.md                            # 客户入口（三句话安装 + 9 工具卡片 + MCP 说明）
├── INSTALL.md                           # ★ AI 自安装协议
├── AGENTS.md                            # 仓库级协作纪律
├── SKILL.md                             # 生成镜像 = skills/devorder-guide/SKILL.md（CI 守卫）
├── .claude-plugin/ + .atomcode-plugin/  # 市场索引（生成物，入库，CI 校验）
├── plugins/devorder-guide/              # 插件副本（纯生成物，不入库）
├── skills/devorder-guide/               # ★ 唯一真源（Agent Skills 标准布局）
│   ├── SKILL.md  README.md  AGENTS.md  .gitignore  pyproject.toml  LICENSE
│   ├── src/  configs/  references/  evals/  scripts/
├── scripts/make_artifacts.py            # 生成器 + 一致性守卫（--check / --build）
├── tests/                               # 开发仓库单测（test_mirror / test_artifacts，不入包）
├── install.sh / install.ps1             # 万能安装器（POSIX / Windows）
├── docs/DEV.md                          # 本文档
├── dist/                                # 生成物：devorder-guide.skill + SHA256SUMS（gitignore）
└── .github/workflows/                   # ci.yml（PR 门禁）+ release.yml（tag 自动发布）
```

## 质量门禁

```bash
bash skills/devorder-guide/scripts/check_all.sh    # 一键七连（ruff → 核心自检 → 契约审计 → 命中回归 → 六位一体 → 分发一致性 → fidelity 自检）
python scripts/make_artifacts.py --check           # 分发一致性（镜像/双市场索引/插件副本 与真源逐字节比对）
python -m pytest tests/ -v                         # 开发仓库单测
```

## 生成器用法

```bash
python scripts/make_artifacts.py --build            # 生成全部产物（根 SKILL.md 镜像 / LICENSE 入包 / plugins 副本 / 双 marketplace / .skill / SHA256SUMS）
python scripts/make_artifacts.py --check            # 只校验已提交状态（CI 门禁）
python scripts/make_artifacts.py --check --tag vX.Y.Z   # 含 tag 版本一致性校验（release.yml 用）
```

`--check` 只校验已提交状态；`--build` 后产物需 `git add` 提交（marketplace.json 入库，plugins/ 与 dist/ 不入库）。

## 版本发布流程

1. 改 `skills/devorder-guide/pyproject.toml` 的 `version` 与 `skills/devorder-guide/SKILL.md` 的 `metadata.version`（两处一致）
2. `bash skills/devorder-guide/scripts/check_all.sh`（全绿）
3. `python scripts/make_artifacts.py --build`
4. `python scripts/make_artifacts.py --check --tag vX.Y.Z`（tag 与包版本必须一致——反向 tag 会被拦截）
5. `git add -A && git commit -m "release: X.Y.Z 分发版"`
6. `git push origin main`
7. `git tag vX.Y.Z && git push origin vX.Y.Z`（release.yml 自动出 Release：.skill + SHA256SUMS）
8. 验证 GitHub Release 资产齐全

## GitCode 镜像（国内客户访问）

```bash
git remote add gitcode https://gitcode.com/YangShen71/devorder-guide.git
git push gitcode main --tags
```

## 上架申请清单

- [ ] `anthropics/claude-plugins-community` PR（官方社区市场，需 CI 校验通过）
- [ ] skills.sh（`npx skills` 检索）注册
- [ ] ClawHub（OpenClaw 市场）提交
- [ ] WorkBuddy SkillHub 提交（需过 skill-vetter，预填 INSTALL.md §6 安全声明）
- [ ] InsCode 官方市场仓 PR（`community + inline` vendor 形态，依赖 CSDN 内部渠道）

## 实测支持矩阵（2026-08-21 T9 真机验收）

验收口径：① AI 自装（粘贴链接/命令安装）② 人工兜底（install.sh / install.ps1 / 复制）③ 触发冒烟（意图预分类 + 引擎判定端到端 5/5 通过：正例触发、反例压制）。引擎级冒烟对全部工具通用（同一引擎 guide_gate.py）。

| # | 工具 | ① AI 自装 | ② 人工兜底 | ③ 触发冒烟 | 备注 |
|---|---|---|---|---|---|
| 1 | Claude Code | ✅ 实测 | ✅ 实测 | ✅ | install.sh/install.ps1 安装后**即时加载**（会话内技能注入验证）；npx skills 建链通道实测 |
| 2 | Codex | ✅ 实测 | ✅ 实测 | ✅ | install.sh → `~/.agents/skills`；npx skills universal（Codex 认 universal 目录） |
| 3 | Cursor | ✅ 实测 | ✅ 实测 | ✅ | npx skills universal 覆盖 Cursor；install.ps1 → `~/.cursor/skills` |
| 4 | Kimi Code | ⚠️ 未装真机 | ✅ 通道就绪 | ✅ | `~/.kimi-code/skills` 已入安装器；whenToUse 字段已加（Kimi 规范字段）；unknown 字段解析行为待真机确认 |
| 5 | OpenClaw | ⚠️ 未装真机 | ✅ 通道就绪 | ✅ | `openclaw skills install git:...` 命令形态见 INSTALL.md；目录通道入安装器 |
| 6 | WorkBuddy | ✅ 实测 | ✅ 实测 | ✅ | install.sh/install.ps1 → `~/.workbuddy/skills`；zip 已更新为当前版；应用内 Git/ZIP 导入动作待补测 |
| 7 | TRAE (CN) | ✅ 实测 | ✅ 实测 | ✅ | npx skills 建 Trae CN 符号链接实测；install.ps1 → `~/.trae-cn/skills` |
| 8 | InsCode Desktop | ⚠️ 依赖 CSDN 内部渠道 | ✅ .skill 可导入 | ✅ | AtomCode 规范 `.atomcode-plugin/marketplace.json` 已生成双份；客户端读取目录实测待上架后补 |
| 9 | GitHub Copilot | ✅ 实测 | — | ✅ | npx skills universal 覆盖 Copilot（+12 工具） |

**实测环境**：Windows 11 + Git Bash + PowerShell 5.1；npx skills 版本为安装时最新。
**待补测项（诚实披露）**：① `gh skill install` 需 GitHub 登录态（本机 gh 未登录）；② Kimi/OpenClaw/InsCode 未安装，其命令形态与 frontmatter 解析（含 `allowed-tools: Bash(python3:*)` 未知字段行为）待真机；③ WorkBuddy 应用内 ZIP/Git 导入动作；④ InsCode 客户端对 `.atomcode-plugin` vs `.claude-plugin` 的读取需上架后实测定唯一正解（当前两者并存，README 以 AtomCode 为主通道声明）。
**T9 修复回环**：install.ps1 两处真机 bug 已修（npx skills 建 Junction 后 `Remove-Item -Recurse` 残留叶子 → 改 `LinkType` 判定只删链接本体；`Copy-Item "src\*"` 目标不存在时 PS5.1 误当叶子 → 先 `New-Item -ItemType Directory`）。
