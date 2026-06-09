# Xcelerator / 工易魔方实时平台证据状态

更新日期：2026-06-09

## 本次已完成的真实平台动作

本次操作均在 Xcelerator AI & API Console 中完成，范围限定为草稿和租户内配置：

| 项目 | 状态 | 说明 |
| --- | --- | --- |
| Wearedge 应用分组 | 已创建 | `Wearedge 工业智能体 PoC`。 |
| Wearedge 应用草稿 | 已创建 | `Wearedge 工业智能体服务`，状态未发布。未保存 AppSecret。 |
| Wearedge API 服务分组 | 已创建 | `Wearedge 工业智能体 PoC`。 |
| API 服务草稿 | 已创建 | `Wearedge Workflow Canvas 协同决策 API`。 |
| API 服务可见范围 | 已设置 | `租户内`，未公开到 AI & API World。 |
| OpenAPI 导入 | 已完成 | 通过 `JSON/YAML导入` 导入 `openapi/wearedge-xcelerator-apiworld.openapi.json`。 |
| API 接口数量 | 已确认 | 3 个接口。 |
| 发布/上架 | 未执行 | 未点击 `保存并发布`，未申请上架。 |

已导入接口：

| Method | Path | 用途 |
| --- | --- | --- |
| GET | `/healthz` | Gateway health and competition metadata. |
| GET | `/v1/edge/runtime-profile` | 展示端侧智能体运行时能力。 |
| POST | `/v1/workflow-canvas/decision` | Workflow Canvas 协同决策主接口。 |

## 证据截图

以下文件位于 `submission-assets/live-evidence/xcelerator/`，该目录默认不进入 Git：

| 文件 | 说明 |
| --- | --- |
| `05-app-group-created.png` | Wearedge 应用分组创建后出现 `注册应用` 入口。 |
| `06-app-registration-draft-filled.png` | Wearedge 应用注册草稿字段。 |
| `07-app-detail-created-redacted-top.png` | 应用详情页顶部裁剪图，避开 AppID / AppSecret 区域。 |
| `08-api-service-basic-info-filled.png` | API 服务基础信息草稿。 |
| `09-api-service-interface-info-step.png` | API 服务进入接口信息步骤。 |
| `10-openapi-json-import-filled.png` | OpenAPI JSON/YAML 导入框已填入规范。 |
| `11-openapi-parse-preview.png` | OpenAPI 解析预览，包含 3 个接口。 |
| `13-openapi-three-apis-imported.png` | 接口列表显示 3 个已导入接口。 |
| `14-api-service-transaction-step-draft.png` | 交易属性页草稿，未发布。 |
| `15-api-service-saved-unpublished-list.png` | API 服务列表确认服务 `未发布`、接口数 `3`、可见范围 `租户内`。 |

## 安全边界

- 未发布 API 服务。
- 未申请公开上架。
- 未保存 AppSecret 或任何密钥。
- 应用详情截图只保留顶部裁剪图，避免保存 AppID / AppSecret 区域。
- API 服务当前使用 PoC 草稿服务器地址，正式调用前需要替换为真实可访问 HTTPS 地址。

## 剩余缺口

| 缺口 | 下一步 |
| --- | --- |
| Gongyi Mofang Workflow Canvas 账号访问 | 当前访问 `https://wfc.bd-iiot.com/` 进入 forbidden 状态，需要平台侧激活或授权。 |
| 真实 HTTPS Wearedge Agent Service | 部署公网 HTTPS 或评审可访问的临时 PoC 网关，再替换服务地址。 |
| Xcelerator 调试调用截图 | 服务地址可访问后，在 Console / API World 中调试 `POST /v1/workflow-canvas/decision` 并截图。 |
| X 认证联调 | 需要由负责人安全保管 AppSecret，不写入仓库；本项目仅保留配置说明。 |
| 企业主体/联系人/IP 承诺 | 由负责人补齐真实公司信息、联系人、承诺材料。 |

## 下一步建议

1. 激活或授权 Gongyi Mofang WFC 账号。
2. 部署 Wearedge Agent Service 到临时 HTTPS 域名。
3. 在 Xcelerator API 服务草稿中替换服务器地址。
4. 执行平台调试调用并保存返回结果截图。
5. 将本次截图纳入演示视频素材和 PoC 证据索引。
