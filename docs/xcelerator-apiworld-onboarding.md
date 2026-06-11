# Xcelerator API World Onboarding Notes

更新日期：2026-06-09

来源：

- <https://developers.siemens-x.com.cn/docCenter/docs/APIWorld/developerguide/TenantsApplyAndAPIServices>
- <https://developers.siemens-x.com.cn/docCenter/docs/APIWorld/manual/app/configure_AppIDSecret>
- <https://developers.siemens-x.com.cn/docCenter/docs/APIWorld/manual/combination/apiservices/pubApiServ>
- <https://developers.siemens-x.com.cn/docCenter/docs/APIWorld/manual/combination/apiservices/subApi>
- <https://developers.siemens-x.com.cn/docCenter/docs/APIWorld/manual/combination/apiservices/serviceCall>

## 文档要点

Xcelerator API World 从账号到 API 服务上线分成三段：

1. 开通企业账号并完成企业认证。
2. 创建应用，配置应用认证，保存、发布并申请上架。
3. 创建 API 服务，录入或导入接口，配置交易属性，发布并申请上架。

平台支持两类账号：

| 账号 | 用途 |
| --- | --- |
| 体验账号 | 手机验证码注册，用于基础功能体验。 |
| 企业账号 | 需要企业资质，拥有完整管理权限。 |

企业账号材料包括企业中英文名称、统一社会信用代码或组织机构代码、企业 logo、行业信息、营业执照、授权委托书、管理员职位、手机号和邮箱。

## 推荐认证方式

优先使用文档中的 **基于 Xcelerator AppID/Secret 的 X 认证**。

调用链路：

```text
订阅方 / 流程 / SDK / Postman
  -> Xcelerator API World 代理地址
  -> X 平台鉴权并加签
  -> 请求头携带 X-TOKEN 转发给 Wearedge Agent Service
  -> Wearedge 调用 /x-api/sign/check 验证 X-TOKEN
  -> 验签通过后处理 /v1/workflow-canvas/decision
```

关键约束：

- X 平台会在代理请求头中携带 `X-TOKEN`。
- 服务商需要使用应用注册时生成的 AppID 作为 `appKey`，调用 `POST https://apig.developers.siemens-x.com.cn/x-api/sign/check`。
- 验签请求体格式为 `{"X-TOKEN": "<token>"}`。
- `X-TOKEN` 有效期为 30 秒。
- `X-TOKEN` 验证成功后立即失效，不能重复验证。
- 验签成功返回 `{"code": 200, "msg": "success", "bizMessage": null}`。
- token 失效时可能返回 `{"code": 400, "msg": "X-TOKEN is expired", "bizMessage": null}`。

Wearedge 当前支持可选 X 认证：

```powershell
$env:WEAREDGE_AUTH_DISABLED="false"
$env:WEAREDGE_XCELERATOR_X_AUTH_ENABLED="true"
$env:WEAREDGE_XCELERATOR_APP_KEY="<Xcelerator AppID>"
$env:WEAREDGE_XCELERATOR_SIGN_CHECK_URL="https://apig.developers.siemens-x.com.cn/x-api/sign/check"
python -m uvicorn jetson.app:app --host 0.0.0.0 --port 8081
```

本地开发仍可使用 `WEAREDGE_AUTH_DISABLED=true` 或 `DEMO_TOKEN`，不影响 `scripts/smoke_workflow_canvas_decision.py`。

## API 服务注册建议值

| 平台字段 | 建议值 |
| --- | --- |
| 应用名称中文 | Wearedge 工业智能体服务 |
| 应用名称英文 | Wearedge Industrial AI Agent Service |
| 应用认证 | 基于 Xcelerator AppID/Secret 认证 |
| 可见范围 | 初期选择租户内；需要共创展示时再公开到 API World |
| 服务中文名称 | Wearedge Workflow Canvas 协同决策 API |
| 服务英文名称 | Wearedge Workflow Canvas Decision API |
| 服务发布路径 | 例如 `/wearedge-industrial-ai-agent`，需平台内全局唯一 |
| 所属应用 | Wearedge 工业智能体服务 |
| 服务标签 | 工业智能体、预测性维护、质量闭环、能源管理、Workflow Canvas |
| 服务器地址 | 对外可访问的 Wearedge Agent Service HTTPS 域名 |
| 服务器路径 | `/v1` |
| 接口后端路径 | `/workflow-canvas/decision` |
| 请求方法 | `POST` |
| 请求体格式 | `application/json` |
| 请求体大小 | 当前 payload 很小，默认 128KB 足够 |
| 流量限制 | PoC 阶段建议 5-10 次/秒；平台默认不限制时最高 40 次/秒 |
| 超时限制 | 建议 5 秒，当前离线决策通常低于 500ms |
| 计费方式 | 初赛/PoC 阶段建议免费 |
| 订阅规则 | 租户内无需上架；公开服务可配置企业认证或人工确认 |

## OpenAPI 导入

API Console 支持 OpenAPI / Swagger 2.0 / 3.0 JSON 或 YAML 导入。

当前可导入文件：

```text
openapi/wearedge-xcelerator-apiworld.openapi.json
```

建议导入后检查：

- 服务路径和接口代理路径是否与平台自动生成值冲突。
- `POST /v1/workflow-canvas/decision` 是否展示请求体 schema。
- `GET /v1/edge/runtime-profile` 是否可作为端侧算力能力展示接口。
- `GET /v1/industrial-agent/solution-profile` 是否可作为工业问题、模型角色、决策机制和验证证据展示接口。
- Header 中是否显示 `X-TOKEN`。
- 返回示例是否包含 `competition_metrics`、`collaborative_decision`、`workflow_canvas`。

## 订阅与调用注意点

订阅方调用服务时：

- 需要先在 API World 订阅服务。
- 订阅成功后获取 appId / appSecret。
- 使用 HTTP 工具调用时需要加入 `appKey` 和 `appSecret` 两个 header。
- 文档特别提醒需要配置 `User-Agent`，否则可能返回 405。
- 服务提供商自己验证服务时不需要走订阅流程，可以使用应用新建时生成的 AppID。

## 当前缺口

| 缺口 | 处理方式 |
| --- | --- |
| 企业账号真实资料 | 由负责人在平台中填写。 |
| HTTPS 公网可访问地址 | PoC 前需要部署 Wearedge Agent Service 或使用临时隧道。 |
| Xcelerator AppID / AppSecret | 应用草稿已创建；AppSecret 不保存到仓库，由负责人安全保管。 |
| 真实平台调用日志 | 使用 API Console 调试调用或流程服务调用后截图/导出。 |
| Gongyi Mofang WFC 访问 | 当前需平台侧激活或授权。 |

## 2026-06-09 实时平台状态

- 已创建 `Wearedge 工业智能体 PoC` 应用分组。
- 已创建 `Wearedge 工业智能体服务` 应用草稿，未发布。
- 已创建 `Wearedge Workflow Canvas 协同决策 API` 服务草稿。
- 已通过 JSON/YAML 导入 `openapi/wearedge-xcelerator-apiworld.openapi.json`。
- 2026-06-09 live 截图中已导入 3 个接口：`/healthz`、`/v1/edge/runtime-profile`、`/v1/workflow-canvas/decision`。
- 2026-06-11 已在 Xcelerator Console 重新通过 `JSON/YAML导入` 导入新版 OpenAPI，API 服务草稿接口数升级为 4，新增 `/v1/industrial-agent/solution-profile`。
- API 服务列表确认：状态 `未发布`，接口数 `4`，可见范围 `租户内`。
- 证据状态文档：`docs/submission/platform-live-evidence-status-20260609.md`。
- 截图目录：`submission-assets/live-evidence/xcelerator/`。
- 未执行发布、公开上架或密钥保存。

## 下一步执行清单

1. 登录 Xcelerator API Console。
2. 创建应用分组和 Wearedge 应用。
3. 选择基于 Xcelerator AppID/Secret 的 X 认证。
4. 保存、发布应用，记录 AppID，先不要把 AppSecret 写入仓库。
5. 注册 API 服务，服务路径建议使用 `wearedge-industrial-ai-agent`。
6. 导入 `openapi/wearedge-xcelerator-apiworld.openapi.json`。
7. 配置服务器地址为可访问的 Wearedge API 域名，服务器路径为 `/v1`。
8. 启动 Wearedge API，启用 `WEAREDGE_XCELERATOR_X_AUTH_ENABLED=true`。
9. 在 API Console 调试 `POST /workflow-canvas/decision`。
10. 截图应用详情、认证配置、API 服务、接口文档、调试返回结果。
