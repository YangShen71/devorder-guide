# devorder-guide 上架申请操作清单（T10 Step 4 交付物）

以下各项均需**用户登录对应平台账号**后手动执行（本机 gh 未登录 GitHub、无 OpenClaw/WorkBuddy 应用操作权限）。全部材料已就绪，照此操作即可。

## 1. anthropics/claude-plugins-community PR（官方社区市场）

- 仓库：`https://github.com/anthropics/claude-plugins-community`
- 方式：fork → 按其 CONTRIBUTING 要求添加条目（引用本仓库 `.claude-plugin/marketplace.json`）→ PR
- 材料：`.claude-plugin/marketplace.json`（已生成，owner=YangShen71，version=0.6.0）
- 前提：该仓库 CI 会校验 marketplace.json 结构；本仓库 ci.yml 已全绿

## 2. skills.sh 注册（npx skills 检索）

- 命令：`npx skills add https://github.com/YangShen71/devorder-guide`（已在本机实测通过）
- 方式：skills.sh 自动从 GitHub 发现；如需人工登记按其文档提交
- 实测：本机 npx skills add 一次打通 15+ 工具（universal: Codex/Cursor/Copilot/Amp/Antigravity +12；symlink: Claude Code/CodeBuddy/Trae CN）——已在 README/DEV.md 声明

## 3. ClawHub（OpenClaw 市场）

- 仓库：ClawHub 市场（OpenClaw 官方市场仓）
- 方式：按其提交规范添加条目，指向 `https://github.com/YangShen71/devorder-guide`
- 材料：README.md（含 9 工具卡片）+ INSTALL.md（AI 自安装协议）

## 4. WorkBuddy SkillHub 提交

- 方式：WorkBuddy 应用内 SkillHub 提交流程
- 前提：需过 skill-vetter（预填 INSTALL.md §6 安全声明：26 工具 DevOrder__* 全量、客户自配 MCP、不含凭据）
- 实测：install.sh/install.ps1 已支持 `~/.workbuddy/skills` 通道；zip 已更新为当前版

## 5. InsCode 官方市场仓 PR（依赖 CSDN 内部渠道）

- 方式：与 DevOrder 团队确认后，按 InsCode 市场仓规范提交（`community + inline` vendor 形态）
- 材料：`.atomcode-plugin/marketplace.json`（AtomCode 规范已生成）
- 备注：InsCode 客户端读取 `.atomcode-plugin/` vs `.claude-plugin/` 的实测定唯一正解，需上架后补测（README 当前以 AtomCode 为主通道声明）

## 状态记录约定

完成一项后在本清单勾选并回填日期；最终状态同步到 docs/DEV.md「上架申请清单」。
