# Xcelerator / 工易魔方实时平台证据状态

更新日期：2026-06-11

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
| API 接口数量 | 已确认 | 2026-06-11 已在 Xcelerator Console 重新导入新版 OpenAPI，服务草稿接口数从 3 升级为 4，新增 `/v1/industrial-agent/solution-profile`。 |
| 发布/上架 | 未执行 | 未点击 `保存并发布`，未申请上架。 |
| Gongyi Mofang WFC 登录 | 已确认 | 2026-06-09 已进入 `https://wfc.bd-iiot.com/projects` 项目页。 |
| Gongyi Mofang WFC 项目 | 已创建 | `Wearedge WFC PoC` 项目已创建并进入编辑器。 |
| WFC 资源配置/工作流入口 | 已截图 | 已保存资源配置页、工作流主画布、编程库和右侧属性/数据表入口截图。 |
| `Wearedge Agent Service` 自定义资源 | 部分完成 | 已拖入 `自定义资源`、命名为 `Wearedge Agent Service`，并添加 `agentHost / Agent Host` 参数；其他参数待补。 |
| WFC Python 程序块定位 | 已完成关键截图 | 2026-06-11 已在 `编程` 库搜索 `Python`，拖入 `Python 程序块` 到画布，属性面板命名为 `CallWearedgeDecisionApi`，源码编辑器 `fb_main.py` 可打开；代码内容和端口绑定仍待最终平台确认。 |
| WFC 数据表字段 | 已完成 DOM verified 证据 | 2026-06-11 已在真实 WFC 项目右侧 `数据表` 中创建 `selected_direction`、`priority`、`recommended_action`、`evidence_summary`、`competition_metrics`、`owner`、`residual_risk`、`approval_status`。内置截图工具裁剪不到右侧弹窗，已保存 DOM verified evidence 图并保留原生截图尝试。 |
| WFC Dashboard 入口 | 部分完成 | 已进入 `https://wfc.bd-iiot.com/dashboard-explorer`；尚未创建 Wearedge 决策 Dashboard。 |
| WFC 运行/日志入口 | 部分完成 | 2026-06-11 已进入 `DEBUG` 状态，执行器显示 `https://spidr.wfc.bd-iiot.com`，运行日志 iframe 显示 `Workflow is ready.`；这证明日志入口和 workflow instance 可用，但还不是 API `ok=true` 成功证据。 |
| Xcelerator 应用主页复核 | 已完成 | 2026-06-11 已重新进入 `https://developers.siemens-x.com.cn/client`，可见 `Wearedge 工业智能体 PoC` 分组和 `Wearedge 工业智能体服务` 应用卡片。 |
| Xcelerator API 详情复核 | 已完成 | 2026-06-11 已进入 API 服务编辑详情，确认服务名、版本、`未发布`、所属应用、可见范围 `租户内`。 |
| Xcelerator 接口列表复核 | 已完成 | 2026-06-11 已在 `接口信息` 步骤复核 4 个接口：`/healthz`、`/v1/edge/runtime-profile`、`/v1/industrial-agent/solution-profile`、`/v1/workflow-canvas/decision`。 |
| WFC `fb_main.py` live-edit 参考源码 | 已入库 | 已新增 `workflows/wfc_call_wearedge_decision_fb_main.py`，用于复制到 WFC Python Function Block；源码调用 `/v1/workflow-canvas/decision`，记录 `wearedge_decision_ok`，不包含账号、token 或密钥。 |

已导入接口：

| Method | Path | 用途 |
| --- | --- | --- |
| GET | `/healthz` | Gateway health and competition metadata. |
| GET | `/v1/edge/runtime-profile` | 展示端侧智能体运行时能力。 |
| GET | `/v1/industrial-agent/solution-profile` | 展示工业问题、模型角色、Agent 分工、KPI 决策机制和验证证据。 |
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
| `11-openapi-parse-preview.png` | 历史 OpenAPI 解析预览，包含 3 个接口。 |
| `13-openapi-three-apis-imported.png` | 历史接口列表显示 3 个已导入接口，保留为操作轨迹。 |
| `14-api-service-transaction-step-draft.png` | 交易属性页草稿，未发布。 |
| `15-api-service-saved-unpublished-list.png` | API 服务列表确认服务 `未发布`、接口数 `4`、可见范围 `租户内`。 |
| `16-openapi-four-apis-imported.png` | 2026-06-11 新版接口列表，显示 4 个接口，包含 `/v1/industrial-agent/solution-profile`。 |
| `24-xcelerator-openapi-parse-result-four-apis.png` | OpenAPI 解析预览显示 4 个接口。 |
| `34-xcelerator-four-apis-saved-unpublished.png` | API 服务编辑页显示 4 个接口，服务仍为未发布。 |
| `35-xcelerator-api-service-list-current.png` | API 服务列表页；DOM 核验显示接口数为 4、状态未发布、可见范围租户内。 |
| `04-runtime-profile-api-test.png` | 临时 HTTPS PoC 网关调用 `/v1/edge/runtime-profile` 的渲染证据；证明外部可达的 Wearedge Runtime API 输出，不等同于已发布的 Xcelerator 代理调用。 |
| `04-runtime-profile-api-test.json` | 与上图对应的原始 JSON 响应，含 `ok=true`、`workflow_canvas_ready=true`、`model_direct_ot_control=false`。 |
| `05-xcelerator-app-home-wearedge-drafts.png` | 2026-06-11 应用主页复核截图，显示 Wearedge 分组和应用草稿入口。 |
| `06-xcelerator-api-detail-basic-info-unpublished.png` | 2026-06-11 API 详情基础信息截图，显示服务名、版本、未发布、所属应用和租户内可见范围。 |
| `07-xcelerator-api-interface-list-four-endpoints-unpublished.png` | 2026-06-11 API 详情接口信息截图，显示 4 个接口均在未发布草稿中。 |
| `07-xcelerator-api-interface-list-four-endpoints-unpublished.dom.json` | 与上图对应的 DOM 摘要，记录 4 个接口行，便于截图不清时复核。 |
| `08-xcelerator-app-home-live-current.png` | 2026-06-11 重新进入应用主页后的复核截图，显示 Wearedge 分组和应用草稿。 |
| `08-xcelerator-app-home-live-current.dom.json` | 与上图对应的 DOM 摘要。 |
| `09-xcelerator-api-basic-info-live-unpublished.png` | 2026-06-11 API 服务基础信息复核，确认仍为 `未发布`、`租户内`。 |
| `09-xcelerator-api-basic-info-live-unpublished.dom.json` | 与上图对应的 DOM 摘要。 |
| `10-xcelerator-api-interface-list-live-four-endpoints.png` | 2026-06-11 API 服务接口信息复核，显示 4 个租户内未启用接口。 |
| `10-xcelerator-api-interface-list-live-four-endpoints.dom.json` | 与上图对应的 4 个接口结构化记录。 |
| `38-xcelerator-client-app-home-current.png` | 2026-06-11 最新应用主页复核截图，显示 `Wearedge 工业智能体 PoC` 分组、`Wearedge 工业智能体服务` 应用卡片和租户内标识。 |
| `38-xcelerator-client-app-home-current.json` | 与上图对应的页面 URL、标题和 DOM 摘要；不包含密钥。 |
| `39-xcelerator-api-detail-current-draft.png` | 2026-06-11 最新 API 详情草稿截图，显示服务名、版本、`未发布`、所属应用、可见范围 `租户内`、服务器地址和 `/v1` 路径。 |
| `39-xcelerator-api-detail-current-draft.json` | 与上图对应的 DOM 摘要；记录草稿边界和无密钥保存说明。 |
| `40-xcelerator-api-interface-list-current-four-endpoints.png` | 2026-06-11 最新接口信息截图，显示 4 个租户内、未启用接口。 |
| `40-xcelerator-api-interface-list-current-four-endpoints.json` | 与上图对应的 4 个接口结构化记录。 |

以下文件位于 `submission-assets/live-evidence/gongyi-mofang/`，该目录默认不进入 Git：

| 文件 | 说明 |
| --- | --- |
| `00-wfc-projects-authenticated.png` | Gongyi Mofang / Workflow Canvas 已登录项目页，显示 `新建空白项目` 入口。 |
| `01-resource-block-wearedge-agent-service.png` | `Wearedge Agent Service` 自定义资源属性面板，已显示 `Agent Host` 参数。 |
| `07-wfc-project-create-form-filled.png` | `Wearedge WFC PoC` 项目创建表单。 |
| `08-wfc-project-created-card.png` | 项目卡创建成功。 |
| `09-wfc-project-editor-opened.png` | 项目编辑器已打开。 |
| `10-wfc-expanded-project-baseline.png` | 扩大视图后的资源配置页，含 `通用工控机.1`。 |
| `11-wfc-workflow-canvas-active.png` | 工作流主画布，含开始节点和运行按钮。 |
| `12-wfc-programming-library-open.png` | 左侧编程功能块库，含资源列表、通用工控机、通用、控制流等分类。 |
| `13-wfc-general-category-expanded.png` | `通用` 分类展开，显示可拖拽通用块。 |
| `14-wfc-general-category-scrolled.png` | 通用块列表滚动，显示 `调用子工作流`、`组`、`注释`、`嵌入图片`、`更新数据表` 等块。 |
| `17-wfc-function-block-properties.png` | 右侧属性面板/大纲视图/数据表入口可见。 |
| `59-wfc-python-search.png` | `编程` 库搜索 `Python`，显示 `编程语言` 分类和 Python 程序块入口。 |
| `67-wfc-python-drag-attempt.png` | Python 程序块早期拖入尝试，保留为操作轨迹。 |
| `02-python-function-block-call-api.png` | 2026-06-11 Python 程序块已拖入画布，属性面板命名为 `CallWearedgeDecisionApi`，源码编辑器可见。 |
| `81-wfc-python-drag-center-attempt.png` | Python 程序块成功拖入画布后的已保存状态。 |
| `86-wfc-python-block-renamed-code-dialog.png` | `CallWearedgeDecisionApi` 命名和源码编辑器同屏证据。 |
| `70-wfc-data-table-entry-attempt-native.png` | 右侧数据表入口原生截图尝试；最终字段表截图仍未完成。 |
| `03-global-data-table-decision-fields.png` | 2026-06-11 DOM verified evidence 图，来自实时 WFC `编辑数据表 -> 自定义数据` DOM，展示 8 个 Wearedge 决策字段；不是伪装成原生截图。 |
| `03-global-data-table-decision-fields.dom.txt` | 与上图对应的实时 DOM 字段记录，保存截图裁剪边界和字段清单。 |
| `92/93/94-wfc-data-fields-*.png` | 原生截图尝试；因内置浏览器只截到左侧画布，保留为审计轨迹。 |
| `71-wfc-dashboard-explorer-entry-native.png` | Dashboard Explorer 入口原生截图尝试；最终 Dashboard 截图仍未完成。 |
| `69-wfc-run-control-attempt-properties.png` | 运行入口点击尝试；没有真实运行日志，不能作为 ok=true 证据。 |
| `95-wfc-debug-state-spidr-open.png` | 2026-06-11 WFC 进入 `DEBUG` 状态，执行器显示 `https://spidr.wfc.bd-iiot.com`；辅助证据，不替代成功运行日志。 |
| `95-wfc-debug-state-spidr-open.dom.txt` | 与上图对应的 DOM 记录。 |
| `96-wfc-run-log-workflow-ready.png` | 2026-06-11 运行日志弹窗辅助证据，iframe 曾读取到 `Workflow is ready.`。 |
| `96-wfc-run-log-workflow-ready.json` | 与上图对应的文字记录和边界说明。 |
| `debug-current-for-coordinate.png` | 2026-06-11 调试态源码只读/坐标排查辅助图，不作为提交核心证据。 |

## 安全边界

- 未发布 API 服务。
- 未申请公开上架。
- 未保存 AppSecret 或任何密钥。
- 应用详情截图只保留顶部裁剪图，避免保存 AppID / AppSecret 区域。
- API 服务当前使用 PoC 草稿服务器地址，正式调用前需要替换为真实可访问 HTTPS 地址。
- `04-runtime-profile-api-test.*` 使用临时 HTTPS PoC 网关证明 Wearedge API 可外部访问；没有把它表述为 Xcelerator 已发布代理调用。

## 剩余缺口

| 缺口 | 下一步 |
| --- | --- |
| `Wearedge Agent Service` 自定义资源参数补齐 | 已创建项目和 `agentHost` 参数；参数编辑器二次添加未稳定成功。下一步补 `agentPort`、`apiKeyRef`、`deploymentMode`、`plantId`、`lineId`，并重新保存资源截图。 |
| Dashboard 截图 | 已进入 Dashboard Explorer 并确认当前返回 `No Dashboard`。前端路由分析显示该页读取 `/api/projects/dashboard-explorer` 并通过 `/remote/preview?...` 预览已有 Dashboard，不是创建入口。下一步需要先运行工作流并从 ui-builder / workflow instance 路径创建可预览看板。 |
| 运行日志截图 | 已有 `Workflow is ready.` 辅助证据；仍需让 `CallWearedgeDecisionApi` 真正执行并调用 Wearedge API，形成 `ok=true`、latency、function blocks 或写表成功日志。 |
| 人工确认截图 | 当前没有平台内 HumanApprovalGate 截图；需要在工作流中添加高风险动作确认/人工确认节点或 Dashboard 确认项。 |
| 真实 HTTPS Wearedge Agent Service | 已用临时 HTTPS PoC 网关完成一次 `/v1/edge/runtime-profile` 外部可达验证；正式提交前仍需稳定域名或平台侧可复现地址。 |
| Xcelerator 调试调用截图 | 已完成临时 HTTPS 网关调用证据；尚未完成 Xcelerator 发布代理路径调用。服务仍保持未发布草稿，不能声称已上架或已通过公开代理调用。 |
| X 认证联调 | 需要由负责人安全保管 AppSecret，不写入仓库；本项目仅保留配置说明。 |
| 企业主体/联系人/IP 承诺 | 由负责人补齐真实公司信息、联系人、承诺材料。 |

## 2026-06-09 WFC 自动化备注

- 已登录 WFC 项目页、创建 `Wearedge WFC PoC` 项目，并保存项目卡、项目编辑器、资源配置页、工作流主画布和编程库截图。
- 当前 WFC 页面大量元素由 canvas 绘制，DOM 不稳定暴露块名、端口和右键菜单。2026-06-11 已确认可以通过“编程搜索 Python -> 从块中心拖入画布 -> 双击打开源码 -> 属性面板改名”的路线创建 `CallWearedgeDecisionApi`。
- 2026-06-11 进一步确认：WFC 处于 `DEBUG` 时源码编辑器只读，会提示 `Cannot edit in read-only editor`。需要先点击调试浮条的 stop 图标，恢复到 `已保存` / `play-circle` 状态，再进行 `fb_main.py` 粘贴保存。
- 文档确认后，Wearedge 最小闭环应走 `通用工控机/SPIDR` -> `自定义资源 Wearedge Agent Service` -> `Python 程序块 CallWearedgeDecisionApi` -> `更新数据表` -> `Dashboard/ui-builder` 的顺序。
- 本项目不会保存 WFC 账号、密码、token 或任何平台密钥。

## 下一步建议

1. 按文档路线在 Gongyi Mofang 创建 `Wearedge Agent Service` 自定义资源。
2. 创建 Wearedge Dashboard/ui-builder 视图，展示指标卡、决策路径、确认项和工作流状态。
3. 部署 Wearedge Agent Service 到临时 HTTPS 域名。
4. 在 Xcelerator API 服务草稿中替换服务器地址。
5. 执行平台调试调用并保存返回结果截图。
6. 将本次截图纳入演示视频素材和 PoC 证据索引。
