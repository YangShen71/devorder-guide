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
git remote add gitcode https://gitcode.com/<owner>/devorder-guide.git
git push gitcode main --tags
```

## 上架申请清单

- [ ] `anthropics/claude-plugins-community` PR（官方社区市场，需 CI 校验通过）
- [ ] skills.sh（`npx skills` 检索）注册
- [ ] ClawHub（OpenClaw 市场）提交
- [ ] WorkBuddy SkillHub 提交（需过 skill-vetter，预填 INSTALL.md §6 安全声明）
- [ ] InsCode 官方市场仓 PR（`community + inline` vendor 形态，依赖 CSDN 内部渠道）

## 实测支持矩阵

真机验收矩阵见计划文档 T9（9 工具 × ① AI 自装 ② 人工兜底 ③ 触发冒烟）；验收结果回填本节，所有宣称以实测为准。
