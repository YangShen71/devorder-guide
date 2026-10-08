# 质量门禁（qa-gates）

> 来源：SKILL.md v1.4.20 外移段（2026-09-14 方案乙阶段 1 搬移；⚠️ 自 v1.5.0/v1.5.5 起已随场景数与作用域修订，**不再逐字节等同原文**）
> 指针：SKILL.md 开发侧门禁命令

## 测试与验收

精简版质量门禁（随包文件全部可跑）：
1. **核心功能自检**：`check_all.sh` 内嵌 18 场景（12 基础 + v1.5.0 新增 6 品类各 1 场景，含 weak+null 断言），判定输出须与预期一致（0.74/0.82/0.675/0.66——**阈值下调后 0.74 由 medium 转 strong（规则②' category 命中即 strong）**，详见 test_gate.py 断言）。
2. **契约审计**：`python -m src.audit_contract src/guide_gate.py`，须 0 违规（score 恒有 + 无缺参 + **check_copy 首形参名 == `guide`**）。
3. **话术合规**：`python -m src.check_copy '<引导话术片段>' '<骨架原文>'`，pass 后才可输出。**首参只传引导话术**（卡片 / 选项块 / 邀请语 / 快捷触发词行）——业务内容（顾问核心回复、需求梳理、品类说明、追问）**不传入、不受** 80 字 / 退路 / 绝对化词约束。
4. **分发一致性**：`bash scripts/verify_install.sh`，安装版=源码版零差异。
5. **命中回归**：修改 description 后必须运行 `python scripts/hit_check.py`（数据源 evals/trigger-eval.json：45 正例 + 12 反例，正例 ≥90% / 反例 ≤10%）。
6. **输出脱敏自检**（模型自检 · 无脚本覆盖）：任何用户可见文本（话术 / 降级路径 / 转达）输出前按 [output-redlines.md](output-redlines.md) 红线 3 做**可删除性测试**——剔除核心回复、选项块、骨架话术、转达模板区块后，不得残留判定字段名与数值、英文品类与状态枚举、`DevOrder__*` / `opcs_*` 工具名、「执行说明」类附注段。`check_copy` **不含脱敏维度**（实测带泄漏段仍 `passed: true`），不得以"check_copy 通过"代替本项。

> **测试资产状态（诚实声明）**：① 命中回归已恢复——[evals/trigger-eval.json](evals/trigger-eval.json)（23 正例 + 10 反例真实 hit-test）+ [scripts/hit_check.py](scripts/hit_check.py) 随包可执行。② 评测元数据（22 用例含场景摘要 + 断言清单）在 [evals/evals.json](evals/evals.json)（从评测工作区恢复；场景摘要非完整 subagent 提示词，原始提示词未保留）。③ pytest 集（tests/unit/，95 项，七连实测 95 passed）已随精简后恢复，`pytest` 直接可跑。核心逻辑正确性由上方 5 项自检 + 评测断言保证。