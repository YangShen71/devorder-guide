# devorder-guide v0.6.0 发布公告（草稿）

## 📦 一句话

DevOrder 对话引导 Skill 正式开源分发：把你的 AI 工具（Claude Code / Codex / Cursor / Kimi Code / OpenClaw / WorkBuddy / TRAE / InsCode Desktop / GitHub Copilot）变成 DevOrder 的发单/接单入口——客户只需粘贴仓库链接即可自动安装。

## 🚀 30 秒安装

1. 复制链接 `https://github.com/YangShen71/devorder-guide`
2. 粘贴到 AI 工具对话框，说「帮我安装这个技能」
3. 弹出权限确认点「允许」——完成

> 安装协议见 INSTALL.md；国内网络不便可用 [GitCode 镜像](https://gitcode.com/yangshen71/devorder-guide)（自动同步）。

## ✨ 本版亮点（0.5.26 → 0.6.0）

- **分发架构定稿**：Agent Skills 标准布局 + 根 SKILL.md 生成镜像 + CI 双门禁（七连质量检查 + 分发一致性校验）——「仓库即真相」；tag 自动发布 Release（.skill + SHA256SUMS）
- **whenToUse 标准字段**：Codex / Cursor / Copilot 的自动触发依据；命中回归 100%/0% 达标
- **万能安装器**：install.sh（macOS/Linux）/ install.ps1（Windows），自动探测 9 工具目录
- **真机验收**：9 工具 × 三动作实测（见 docs/DEV.md 实测支持矩阵）；npx skills 一次打通 15+ 工具；修复 install.ps1 两处真机 bug

## 📦 产物

- GitHub Release 资产：`devorder-guide.skill` + `SHA256SUMS`
- 市场索引：`.claude-plugin/marketplace.json`（Claude Code 插件通道）+ `.atomcode-plugin/marketplace.json`（AtomCode/InsCode 通道）

## ⚠️ 运行依赖

- Python 3.10+（引擎为确定性判定脚本）
- DevOrder MCP（26 工具，`mcp__DevOrder__*`）——客户方自行配置，仓库不含任何凭据

## 反馈

- 问题/建议 → GitHub Issues
- DevOrder 平台内反馈 → 平台客服
