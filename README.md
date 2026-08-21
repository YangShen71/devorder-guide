# devorder-guide

DevOrder（CSDN 开发者服务交易平台）对话引导 Skill——在 AI 工具自然对话中识别用户的开发者服务需求（开发者增长/用户招募/内容创作/内容分发/广告投放/技术会议/开发者大赛/训练营/线上实操/线下活动/社区运营，11 类，与 SKILL.md description 一致），确定性判定是否引导发单/接单，用 DevOrder MCP 工具闭环。

## 🚀 30 秒安装（普通客户版）

1. 复制本仓库链接：`https://github.com/<owner>/devorder-guide`
2. 粘贴到你的 AI 工具对话框（Claude Code / Codex / Cursor / Kimi Code / OpenClaw / WorkBuddy / TRAE 等）
3. 说「帮我安装这个技能」，AI 会自动完成——**弹出权限确认时点「允许」即可**

安装协议见 [INSTALL.md](INSTALL.md)；网络不便可用 [GitCode 镜像](https://gitcode.com/<owner>/devorder-guide)。

## 各工具安装与触发（9 张卡片，含手动兜底）

| 工具 | AI 自装 | 触发方式 | 手动兜底 |
|---|---|---|---|
| Claude Code | ✅ | 对话自动触发 | `~/.claude/skills/` |
| Codex | ✅ | 对话自动触发 / `$devorder-guide` | `~/.agents/skills/` |
| Cursor | ✅ | 对话自动触发 | `~/.cursor/skills/` |
| Kimi Code | ✅ | 自动触发 / `/skill:devorder-guide` | `~/.kimi-code/skills/` |
| OpenClaw | ✅ | 对话自动触发 | `~/.openclaw/workspace/skills/` |
| WorkBuddy | ✅（Git 导入） | 对话自动触发 | ZIP 导入 / SKILL.md 拖拽 |
| TRAE | ⚠️ 人工导入 | 对话触发（需开技能开关） | 设置→技能与命令→上传 `.skill` |
| InsCode Desktop | ⏳ 市场申请中 | — | 复制技能目录 |
| GitHub Copilot | ✅ | 对话自动触发 | — |

## ⚠️ 运行依赖（安装前须知）

- **Python 3.10+**：引擎为确定性判定脚本 `python src/guide_gate.py`
- **DevOrder MCP**：发单/接单闭环需要 DevOrder MCP 服务（26 个工具，`mcp__DevOrder__*`），**由客户方自行配置**，本仓库不含任何凭据
- Windows 下含中文输出的脚本需 `PYTHONUTF8=1`（已内置处理）

## 开发与发布

构建/质量门禁/发布流程见 [docs/DEV.md](docs/DEV.md)；一键门禁：`bash skills/devorder-guide/scripts/check_all.sh`。

## License

Proprietary（© CSDN DevOrder）。可免费下载使用，禁止二次分发用于竞争性用途。
