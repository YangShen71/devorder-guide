# AGENTS.md — 仓库协作纪律（分发仓库级）

## 一、内容真源

- `skills/devorder-guide/` 是唯一内容真源（Agent Skills 标准布局）；根 `SKILL.md`、`plugins/`、`dist/`、`marketplace.json` 均为**生成物**。
- 生成物纪律：禁止手工编辑生成物；改真源后必须 `python scripts/make_artifacts.py --build` 再 `--check`。
- 根目录零散落：`.gitignore / AGENTS.md / LICENSE / README.md / INSTALL.md / SKILL.md(镜像) / scripts/make_artifacts.py` + 子目录（docs/、skills/、plugins/、.claude-plugin/、.atomcode-plugin/、tests/、.github/）。

## 二、质量门禁（变更后必跑，全部从仓库根执行）

- 技能侧全量：`bash skills/devorder-guide/scripts/check_all.sh`
- 分发一致性：`python scripts/make_artifacts.py --check`（CI 同款门禁）
- 单条命令以包目录为 cwd：`cd skills/devorder-guide && python -m src.audit_contract src/guide_gate.py`

## 三、版本纪律

- 版本真源 = `skills/devorder-guide/pyproject.toml`；改版须同步 SKILL.md `metadata.version` + git tag，三者一致（`--check --tag vX.Y.Z` 验证）。

## 四、发布

- 流程见 [docs/DEV.md](docs/DEV.md)；`vX.Y.Z` tag 触发 release.yml 自动发布（.skill + SHA256SUMS 资产）。
