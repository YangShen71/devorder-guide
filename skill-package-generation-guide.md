# Skill 包编写与版本更新约定

本文档用于指导 Skill 包编写和发布，不面向最终用户。Skill 编写者应按本文档约定组织文件、声明版本，并在 `SKILL.md` 中提供 Harness 可识别的版本检查和更新说明。

## 1. Skill 包结构

最小 Skill 包只需要包含一个 `SKILL.md`：

```text
skill-name/
└── SKILL.md
```

内容较多时，可以按需拆分参考文件：

```text
skill-name/
├── SKILL.md
├── references/
│   ├── tool-routing.md
│   └── safety-rules.md
└── examples/
    └── examples.md
```

约定：

- `SKILL.md` 必须位于压缩包根目录下的 Skill 目录中。
- `SKILL.md` 是 Harness 首先读取的入口文件。
- 版本、身份和基本描述写在 `SKILL.md` 的 frontmatter 中。
- 详细规则可以放在 `references/` 下，由 `SKILL.md` 引用。
- 不要在 Skill 包中写入 API Key、JWT、密码或其他生产凭据。
- 不要把平台完整工具 schema 固化在 Skill 中，工具参数以当前 MCP Server 返回的 schema 为准。

运营端支持上传 `.zip` 和 `.tar.gz` 文件。建议压缩包展开后的目录结构保持如下形式：

```text
opcs-client-skill-1.2.0.zip
└── opcs-client-skill/
    └── SKILL.md
```

## 2. 身份标识

Skill 包按使用身份分别管理。当前支持以下身份值：

| 身份 | 取值 | 说明 |
| --- | --- | --- |
| 发单方 | `CUSTOMER` | 面向发单用户的 Skill |
| 接单方 | `CONTRACTOR` | 面向接单用户的 Skill |

`SKILL.md` 中的 `identity` 应与运营端上传时选择的身份保持一致：

```yaml
identity: CUSTOMER
```

同一身份下，平台只保留一个 `ACTIVE` 版本。上传新版后，该身份下原有版本自动变为 `DISABLED`。已禁用版本不能通过下载接口获取。

## 3. 版本号写法

版本号使用三段式语义化版本：

```text
主版本.次版本.修订版本
```

示例：

```text
1.0.0
1.1.0
1.1.1
2.0.0
```

建议按以下规则递增：

- `1.0.0`：首次发布。
- `1.1.0`：新增能力或新增非破坏性规则。
- `1.1.1`：修正文案、示例或非破坏性错误。
- `2.0.0`：工具名称、调用方式、角色边界等发生不兼容变化。

版本号必须同时出现在以下位置，并保持一致：

1. `SKILL.md` 的 `version` 字段。
2. 运营端上传表单填写的版本号。
3. Harness 本地记录的当前版本号 `currentVersion`。

示例：

```yaml
name: devorder-client-brief
version: 1.2.0
identity: CUSTOMER
description: DevOrder 发单方需求梳理 Skill
```

当前运营端不会自动读取并校验压缩包内的 `version` 字段。版本号由上传者在运营端单独填写，因此上传时必须人工确认两处版本号一致。同一身份下，`identity + version` 不允许重复上传。

## 4. 最新版本查询接口

Harness 应在启动时或按自身更新策略定期查询指定身份的最新 Skill 版本：

```http
GET /api/v1/skills/version?identity={identity}&currentVersion={currentVersion}
```

参数说明：

| 参数 | 必填 | 取值 | 说明 |
| --- | --- | --- | --- |
| `identity` | 是 | `CUSTOMER` / `CONTRACTOR` | 当前 Skill 对应身份 |
| `currentVersion` | 是 | 语义化版本号 | Harness 当前已加载的版本 |

发单方示例：

```http
GET https://example.com/api/v1/skills/version?identity=CUSTOMER&currentVersion=1.1.0
```

接单方示例：

```http
GET https://example.com/api/v1/skills/version?identity=CONTRACTOR&currentVersion=1.1.0
```

该接口为公开接口，当前不需要 `Authorization` 或 `X-API-Key` 请求头。

成功响应中的 `data` 示例：

```json
{
  "identity": "CUSTOMER",
  "currentVersion": "1.1.0",
  "latestVersion": "1.2.0",
  "latestId": 123,
  "downloadUrl": "/api/v1/skills/123/download",
  "forceUpdate": false,
  "changelog": "补充需求澄清规则"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `identity` | 返回结果对应的身份 |
| `currentVersion` | 请求中传入的本地版本 |
| `latestVersion` | 平台当前生效版本 |
| `latestId` | 平台当前生效版本的 Skill 包 ID |
| `downloadUrl` | 当前生效版本的下载地址 |
| `forceUpdate` | 是否要求强制更新，当前为预留字段 |
| `changelog` | 最新版本更新说明 |

无生效版本时返回 `404`；身份参数不合法时返回 `400`。

## 5. 下载接口

Harness 不应根据版本号自行拼接下载地址，应使用版本查询接口返回的 `downloadUrl`。

当前下载接口为：

```http
GET /api/v1/skills/{id}/download
```

示例：

```http
GET https://example.com/api/v1/skills/123/download
```

接口返回 Skill 压缩包文件流，当前支持的文件类型为 `.zip` 或 `.tar.gz`。只有 `ACTIVE` 版本可以下载，已禁用版本返回 `404`。

如果需要直接根据 Skill 信息查询后再下载，可以使用：

```http
GET /api/v1/skills/latest?identity=CUSTOMER
```

该接口返回指定身份当前生效版本的元数据。用户端页面目前使用该接口获取版本信息，再使用 `id` 调用下载接口。

## 6. Harness 自动更新约定

Skill 应在 `SKILL.md` 中告诉 Harness：

1. 本地当前版本是什么。
2. 使用哪个身份值查询版本。
3. 版本查询接口的路径和参数。
4. 从响应的 `downloadUrl` 下载新包。
5. 下载后校验新包中的版本号，再替换本地 Skill。
6. 更新本地版本记录，并重新加载 Skill。

推荐判断逻辑：

```text
调用版本查询接口
    |
    v
比较 latestVersion 与 currentVersion
    |
    +-- 相同：继续使用当前 Skill
    |
    +-- 不同：读取 downloadUrl
                |
                v
          下载新 Skill 包
                |
                v
          校验并替换本地 Skill
                |
                v
          更新 currentVersion 并重新加载
```

更新时建议先写入临时文件或临时目录，完成下载和基本校验后再替换现有 Skill，避免网络中断导致本地 Skill 不完整。

`forceUpdate` 当前为预留字段。若后续返回 `true`，Harness 应优先完成更新，再继续执行依赖该 Skill 的任务。

自动更新能力取决于目标 Harness 是否允许访问网络、写入本地 Skill 目录以及重新加载 Skill。不能自动更新的 Harness，应由外部安装器或运维脚本执行同样的版本检查和替换逻辑。

## 7. `SKILL.md` 最小示例

以下示例只展示版本声明和自动更新约定，业务规则可按实际 Skill 补充：

```markdown
---
name: devorder-client-brief
version: 1.2.0
identity: CUSTOMER
description: DevOrder 发单方需求梳理 Skill
---

# DevOrder 发单需求梳理

## Skill 元数据

- 当前版本：`1.2.0`
- 适用身份：`CUSTOMER`
- 版本查询接口：`GET /api/v1/skills/version`
- 下载接口：使用版本查询响应中的 `downloadUrl`

## 版本检查与自动更新

当前 Skill 版本为 `1.2.0`。

Harness 启动时或按更新策略调用：

```http
GET https://example.com/api/v1/skills/version?identity=CUSTOMER&currentVersion=1.2.0
```

读取响应中的 `latestVersion` 和 `downloadUrl`：

- `latestVersion` 与 `1.2.0` 相同：继续使用当前 Skill。
- `latestVersion` 与 `1.2.0` 不同：使用 `downloadUrl` 下载最新 Skill 包。
- 下载完成后，校验新包内 `SKILL.md` 的 `version` 是否等于 `latestVersion`。
- 校验通过后替换本地旧版本，并重新加载 Skill。
- 不要根据版本号自行猜测或拼接下载地址。

版本查询响应示例：

```json
{
  "identity": "CUSTOMER",
  "currentVersion": "1.2.0",
  "latestVersion": "1.3.0",
  "latestId": 124,
  "downloadUrl": "/api/v1/skills/124/download",
  "forceUpdate": false,
  "changelog": "补充需求澄清规则"
}
```

最新版本下载地址由服务端返回，例如：

```http
GET https://example.com/api/v1/skills/124/download
```

## 业务规则

在此处编写本 Skill 的角色边界、工具调用规则、输入要求和输出约束。
```

## 8. 发布前检查

上传运营端前至少检查以下内容：

- 压缩包可以正常解压。
- `SKILL.md` 位于约定目录中。
- `name`、`version`、`identity` 字段存在且格式正确。
- `SKILL.md` 内版本号与运营端填写的版本号一致。
- `identity` 与运营端选择的身份一致。
- 版本查询接口中的 `identity` 与 Skill 身份一致。
- Skill 中使用的是 `/api/v1/skills/version` 版本查询接口。
- 更新时使用服务端返回的 `downloadUrl`，没有硬编码某个版本的下载地址。
- 包内没有 API Key、JWT、密码或其他生产凭据。
- Skill 未声明不存在的工具或接口。
