# AGENTS.md — AI 协作纪律

> devorder-guide Skill 的 AI 协作纪律（精简版，删除开发过程历史）。

## 一、项目铁律

1. **TDD 铁律**：测试先行（全红）→ 实现补全（全绿）→ 重构 → 故意改坏验证（确认测试真兜底）。
2. **六位一体同步**：Spec / 实现 / 测试 / 文档 / 示例 / 配置 讲同一个故事；六位任一处变更必须同步其余五位。
3. **红线纪律**：① 验收结果基于真实完成证据，禁止提前宣称完成 ② 评分修正历史重放验证 ③ 主观断言人工复核 ④ 契约变更六位一体同步 ⑤ **声明必须实测背书** ⑥ 红了不能 merge ⑦ DevOrder MCP 字段推断二次核对 ⑧ DevOrder MCP 错误码兜底 ⑨ userConfirmation 硬门禁 ⑩ 命中回归防漂移。
4. **简明优先**：单次使用逻辑不抽象封装、不新增未来扩展；只解当下问题。
5. **外科手术式修改**：只改任务必需代码；不格式化/重构无关内容；遵循项目现有风格。
6. **目标驱动**：动手前定义可验收的成功标准，每步完成后主动校验；多步任务列出计划（步骤 → 验证）。

## 二、目录规则

- **根目录零散落**：仅 `.gitignore/AGENTS.md/LICENSE/pyproject.toml/SKILL.md` 5 项入口 + 子目录。
- **测试工件不出根**：临时日志/缓存文件禁止放项目根（会被 `.skill` 打包）。

## 三、质量门禁（变更后必跑）

| 项 | 命令 |
|---|---|
| 风格 | `ruff check src/ --no-cache`（精简版无 tests/）|
| 核心自检 | `python scripts/hit_check.py`（命中回归）+ check_all 内嵌 12 场景 |
| 契约审计 | `python -m src.audit_contract src/guide_gate.py` |
| 话术合规 | `python -m src.check_copy '<话术>' '<骨架>'` |
| 六位一体 | `python -m src.pipeline` |
| 分发一致性 | `bash scripts/verify_install.sh` |
| **交付纪律（复审 N7）** | **发布任何「终态数字」（行数/审计/包大小/文件数）前，先跑 `bash scripts/check_all.sh` 读末尾「实测数字」段，以实测为准**——禁止凭记忆/估算写声明 |
| 一键六连 | `bash scripts/check_all.sh`（精简版唯一入口，开发仓库有 pytest 全量可恢复）|

## 四、SKILL.md 维护纪律

1. description ≤150 字（超长必须标注例外，且不牺牲 MUST_COVER 10 代表词）。
2. 正文只放高频指令；低频细节外链 references/，**禁止大段复制 references 全文**。
3. references 按需加载——以链接引用，AI 使用时按需读取。
4. 改 description 必跑命中回归（`python scripts/hit_check.py`，正 ≥90%/反 ≤10%；数据源 evals/trigger-eval.json：23 正例 + 10 反例）。

## 五、分发一致性纪律（红线）

任何 src/ / references/ / configs/ / evals/（若保留）变更后必须重新打包安装——**「安装版=源码版」是分发状态的唯一事实**：
- 变更 → 必跑 `bash scripts/verify_install.sh`（打包 → 覆盖安装 → diff 复验）
- 零差异才可宣称已分发；任何差异 → 禁止宣称，重新打包
- 禁止手工单向同步源码/安装版
- 每批次验收前先跑 verify_install

## 六、禁止事项

- 禁止先实现后补测试 / 禁止虚构测试口径 / 禁止无评审改 Spec / 禁止魔法数字（应在 configs/constants.json）
- 禁止对原始 PDF/DOCX/源文件做不可逆覆盖
- 禁止发布未签字的 Skill

---

*活文档：发现规则漏洞或新约束时立即追加。*