# devorder-guide 安装协议（INSTALL.md）

> 本文件同时服务两种读者：**AI 代理**（用户粘贴仓库链接时，请先执行下方「AI 安装协议」）与**人类**（无 AI 场景的手动安装）。

## ⚡ AI 安装协议（请 AI 代理按顺序执行）

当用户给你本仓库链接（`https://github.com/YangShen71/devorder-guide`）并要求安装技能时：

1. **先探测环境**：`python3 --version`（Windows 试 `py -3 --version` 或 `python --version`）。若 < 3.10 或缺失，向用户说明技能引擎需要 Python 3.10+，并询问是否安装（推荐：`winget install Python.Python.3.12` 或官网 python.org）。
2. **按下方「通道表」选定通道执行**。执行命令前会看到权限确认——**这是正常的安全机制，请等待用户批准后继续，不要放弃**。
3. **执行验收清单**（见 §3），向用户汇报三项：装到了哪个工具、怎么触发、还缺什么（Python / DevOrder MCP 等）。
4. 若 GitHub 访问失败（国内网络常见），改用镜像：`https://gitcode.com/YangShen71/devorder-guide`。

## 通道表（AI 优先，人工兜底在 §4）

| 工具 | 首选通道（AI 执行） | 人工兜底 |
|---|---|---|
| Claude Code | `gh skill install YangShen71/devorder-guide devorder-guide --agent claude-code --scope user`；无 gh 2.90+ 则 `npx skills add YangShen71/devorder-guide -s devorder-guide -a claude-code -g -y` | 复制 `skills/devorder-guide/` 到 `~/.claude/skills/` |
| Codex | `gh skill install YangShen71/devorder-guide devorder-guide --agent codex --scope user`；装完运行 `codex features list`，若 skills 未启用执行 `codex --enable skills`，并重启 Codex | 复制到 `~/.agents/skills/`（或旧版 `~/.codex/skills/`） |
| Cursor | `gh skill install YangShen71/devorder-guide devorder-guide --agent cursor --scope user` | 复制到 `~/.cursor/skills/`（Cursor 不支持符号链接，必须复制） |
| Kimi Code | 复制到 `~/.claude/skills/`（Kimi 会扫描该目录）或 `~/.kimi-code/skills/` | 同上；装后可用 `/skill:devorder-guide` 手动调用 |
| OpenClaw | `openclaw skills install git:YangShen71/devorder-guide` | 复制到 `~/.openclaw/workspace/skills/devorder-guide` 后 `openclaw restart` |
| WorkBuddy | 告知用户：主界面 → 头像 → Claw设置 → 技能管理 →「从Git仓库导入」→ 粘贴仓库链接 | 下载 Release 的 `.skill` 包 ZIP 导入，或把 SKILL.md 拖进聊天框 |
| TRAE | 无法 AI 一键安装，走人工：设置 → 技能与命令 → 创建 → 上传 `devorder-guide.skill`（Release 资产）或复制到 `~/.trae-cn/skills/`（国内版） | 同上；或 `npx skills add YangShen71/devorder-guide -s devorder-guide -a trae -g -y` |
| InsCode Desktop | 暂走插件市场：`/plugin marketplace add https://gitcode.com/YangShen71/devorder-guide.git`（需上架后可用，见 README） | 复制到 InsCode 技能目录（AtomCode 规范，路径以客户端文档为准） |
| GitHub Copilot | `gh skill install YangShen71/devorder-guide devorder-guide --agent github-copilot --scope user` | — |

> 说明：`gh skill` 需要 GitHub CLI ≥ 2.90（`gh --version` 检查；安装：`winget install GitHub.cli`）。`npx skills` 需要 Node.js。`-a` 后的 agent 名以 `npx skills add --help` 当前支持列表为准，个别工具如不支持就用「复制」通道。

## §3 验收清单（AI 与人类共用）

装完后逐项确认，缺一项都要向用户说明：

1. 技能目录存在且包含引擎：`<技能目录>/devorder-guide/src/guide_gate.py`、`configs/constants.json`、`references/category-enum.md`
2. Python ≥ 3.10（`python3 --version`；Windows 试 `py -3 --version` 或 `python --version`——引擎是 `python src/guide_gate.py`，无 Python 则装了也用不了）
3. 触发方式已告知用户（各工具不同，见 §5）

## §4 人工安装（无 AI 场景）

1. 打开 https://github.com/YangShen71/devorder-guide/releases ，下载最新 `devorder-guide.skill`
2. 按上表「人工兜底」列把包放进对应技能目录，或按工具 UI 导入
3. 验验收清单 §3

## §5 各工具触发方式（安装完怎么用）

- Claude Code / Codex / Cursor / Copilot：直接对话表达开发者服务需求（开发者增长/用户招募/内容创作/内容分发/广告投放/技术会议/开发者大赛/训练营/线上实操/线下活动/社区运营），description 命中即自动触发
- Kimi Code：对话表达需求，或 `/skill:devorder-guide` 手动调用
- OpenClaw：对话表达需求，或在 Web UI 里说明想用「DevOrder 对话引导」技能
- WorkBuddy / TRAE：对话触发；TRAE 需确认技能开关已打开（设置 → 技能与命令）

## §6 安全声明

- 本仓库所有脚本来源为 CSDN DevOrder 团队，仅执行「触发判定」与「话术校验」两类逻辑，不访问网络、不读取敏感目录（`~/.ssh`、凭据文件等）
- 引擎依赖 DevOrder MCP 服务（26 个查询/下单工具，MCP 工具名 `mcp__DevOrder__*`），**MCP 需客户方自行配置**，本技能不包含任何凭据
- 安装时若安全扫描器（如 WorkBuddy skill-vetter）提示 Bash 权限，属预期：引擎通过 Bash 运行 `python3 src/guide_gate.py` 做确定性判定

## §7 常见问题

- **权限确认弹窗**：正常。AI 需要执行安装命令/运行 python，请点击允许
- **GitHub 打不开**：用 GitCode 镜像 `https://gitcode.com/YangShen71/devorder-guide`，或下载 Release 资产人工导入
- **装了不触发**：先确认 Python ≥ 3.10；再确认技能开关/目录正确；还不行就到本仓库 Issues 提问
