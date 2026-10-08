# 版本检查详细脚本（version-check-detail）

> **何时读取本文件**：更新流程已固化为 [scripts/update_apply.py](scripts/update_apply.py)（方案 A 自动执行）；本文件仅存结论表与 B-2/B-4 重载细则。
## 结论与行动

| 输出 | 行动 |
|---|---|
| `GO:vX ...` | 静默继续，进入第 1 步意图预分类 |
| `UPDATE:vY DL=... FORCE=...` | 自动调用 scripts/update_apply.py 完成更新（下载→校验→替换→收尾）；成功后按 B-2 强制动作重载 |
| `SKIP:vX (...)` | 本地领先平台（防降级），静默继续用本地版 |
| `NO_VERSION_FOUND`（exit 2） | 本地 SKILL.md frontmatter 缺 version → 视为包损坏，告知用户重新安装 Skill |
| `USAGE_ERROR`（update_apply 内部护栏） | 缺 --dl/--latest 参数——仅脚本内部护栏，version_check 恒传全参数，宿主不会看到 |
| `NO_VERSION_FOUND`（exit 2） | 本地 SKILL.md frontmatter 缺 version → 视为包损坏，告知用户重新安装 Skill |
| `DIR_IS_BACKUP:xxx` | 一句话告知用户「检测到从备份目录加载（宿主未刷新），建议重启宿主加载最新版」，跳过更新流程，继续按当前版本执行 |
| `SENTINEL_MISMATCH` + `RELOAD_HINT` | 从 RELOAD_HINT 绝对路径读取 SKILL.md 并以其为准继续处理当前请求 |

> ⏹ **happy path 读到这里即可停止**；仅当 version_check.py 输出 `UPDATE` 时继续往下读（自动执行 update_apply.py / B-2 / B-4）。

> ⏹ **更新执行已固化**：[scripts/update_apply.py](scripts/update_apply.py)（唯一权威，version_check 检测到 UPDATE 时自动调用，下载→校验→替换→收尾三件套含 session 状态迁移）；本文件不再存更新脚本。
## B-2 更新成功后的强制动作（要点）

看到 `RELOAD_REQUIRED` 信号后：① 立即停止按当前（旧版）Skill 逻辑继续执行；② 尝试重新加载本 Skill（宿主 Skill 加载入口）；③ 重新读 SKILL.md frontmatter `version`，等于 `UPDATED_TO` 即重载成功 → 继续处理当前请求（用户无感知）；④ 重载不成功（宿主返回缓存版）→ 告知用户「检测到新版本 v{LATEST} 已完成更新，本会话仍运行旧版，请重启会话立即生效」。

## B-4 forceUpdate 形式化（要点）

若 version_check.py 输出中 `FORCE=True`：① update_apply.py 自动完成更新；② 输出 `FORCE_RELOAD_REQUIRED`；③ 按 B-2 强制动作重载；④ 无法重载时告知用户「平台要求强制更新，已完成更新，请重启会话立即生效」，本会话按当前逻辑继续（不阻断）。

## 哨兵自愈说明（脚本已内化，模型无需关注）

哨兵缺失/损坏/版本漂移时，version_check.py 内部自动以 frontmatter 版本重建哨兵（C-2c 自愈）并继续——不再输出 SENTINEL_MISSING/CORRUPT/DRIFT/REBUILT 信号。
