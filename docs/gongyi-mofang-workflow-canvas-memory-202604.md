# 工易魔方 Workflow Canvas 平台记忆卡

更新日期：2026-06-09

## 资料来源

本记忆卡来自 2026-04 版工易魔方资料包和 WFC 文档包，用于 Wearedge 工业智能体参赛 PoC、接入说明和演示证据准备。

| 文件 | 重点用途 |
| --- | --- |
| 附件1-工易魔方-让人工智能触手可及 完整版 202604.pdf | 平台定位、低代码工作流、IT/OT 融合、3D 仿真、边缘部署与典型场景 |
| 附件2-工易魔方用户注册及账号激活指南onepage.pdf | 注册、账号激活和学习入口 |
| 附件3-工易魔方onepage简介.pdf | 平台价值、支持对象、部署模式、二次开发、AI Agent 兼容性 |
| 附件4-工易魔方学习园地客户使用指南.pdf | 学习园地入口和客户自助学习路径 |
| 第十一届“创客中国-开发工具套件工易魔方推荐.docx | 赛事工具推荐、免费账号、试用一体机和赛题建议 |
| WFC000_文档列表.docx | WFC 文档包索引 |
| WFC001_工易魔方工作说明书.docx | Workflow Canvas 主说明、资源配置、功能块、调试、数据表 |
| WFC002_蜘蛛执行器使用手册.docx | PC/NUC 端 Spider 执行器连接方式 |
| WFC003_IPC使用手册.docx | 西门子 Edge IPC 上的执行器/资源连接方式 |
| WFC004_Workflow Canvas Crash Course.docx | Workflow Canvas 快速课程和基础操作 |
| WFC005_如何对资源块及功能块进行二次开发.docx | 自定义资源块/功能块开发、`info.json`、打包上传 |
| WFC006_资源块安装使用.pdf | 资源块安装和使用 |
| WFC007_ 如何保存数据，如何在ui-builder上展示图片.docx | Python 输出 JSON、全局数据表、ui-builder 数据绑定 |
| WFC008_V3D支持的格式.docx | V3D 可用 3D 模型格式 |
| WFC009_基础方法解释.pdf | V3D 方法和仿真对象 API |
| WFC010_工易魔方快速入门手册V2.pdf | 登录、建项目、部署到 Spider、日志和机器人示例 |

## 一句话记忆

工易魔方不是单纯的看板或脚本容器，而是把资源配置、低代码流程编排、Python/JS/C/C++/Rust 等扩展、Spider 边缘执行器、全局数据表、Dashboard/ui-builder 和 V3D 仿真串在一起的 IT/OT 工作流工程平台。Wearedge 的参赛表达应该是：把 Wearedge 多智能体决策服务封装成工易魔方可调用、可部署、可观察、可人工确认的 Workflow Canvas 资源块/功能块组合。

## 平台能力记忆

| 能力 | 对 Wearedge 的意义 |
| --- | --- |
| 资源配置 | 把 Wearedge Agent Service、MES/质量/能耗/设备数据源、IPC/Spider 执行器配置成可复用资源。 |
| Workflow Canvas | 用拖拽流程表达“读取上下文 -> 调用智能体 -> 协同决策 -> 人工确认 -> 写入数据表 -> Dashboard 展示”。 |
| 自定义功能块 | 用 Python Function Block 调用 `/v1/workflow-canvas/decision`，并把响应作为 JSON 输出。 |
| 自定义资源块 | 后续可将 Wearedge 连接信息打包为资源块，使用 `info.json` 描述参数、类型和资源绑定。 |
| 全局数据表 | 存储主方向、优先级、建议动作、证据、指标、残余风险、人工确认状态。 |
| Dashboard / ui-builder | 展示指标卡、决策路径、确认项、工作流状态，也可展示 JSON 中的图片 URL 或证据链接。 |
| Spider / SPIDR 执行器 | 将云端/本地 Workflow 部署到 PC、NUC 或 IPC，形成边缘运行证据。 |
| 3D / V3D | 用数字化产线仿真展示换型、AGV、输送线、机器人、碰撞检测和状态回放。 |
| 工业协议和 OT 设备 | 平台资料覆盖 OPC UA、MQTT、BACnet、PLC、机器人、AGV、相机、传感器等，但 Wearedge 初赛 PoC 应避免直接自动写 OT。 |
| Web IDE / Git / Gallery | 可把已有 AI 算法封装复用，适合赛事材料中强调联合共创和组件复用。 |

## Wearedge 接入原则

1. Wearedge 先作为 `Wearedge Agent Service` 被 WFC 调用，不直接替代 WFC 的资源/执行器。
2. WFC Python Function Block 只负责组装上下文、发 HTTP 请求、校验响应、输出 JSON。
3. 高风险动作必须经过 `HumanApprovalGate`，不得由模型或 Python Function Block 直接写 PLC/机器人控制。
4. 决策结果先写全局数据表，再进入 Dashboard/ui-builder 展示，形成可截图证据。
5. 若暂时没有真实产线，先用模拟 MES、设备、质量、能耗和 WFC context 表；文档中明确标注“离线/模拟 PoC”。
6. 如果 Xcelerator API World 代理 Wearedge API，则保留 `/v1/workflow-canvas/decision` 兼容接口，只在网关层增加认证和 OpenAPI 导入。

## WFC 操作检查清单

| 步骤 | 必须形成的证据 |
| --- | --- |
| 登录 `https://wfc.bd-iiot.com/` 并确认账号激活 | 登录/项目首页截图，若未激活需记录已联系平台团队 |
| 创建 Wearedge PoC 项目和 Workflow | 项目列表、Workflow Canvas 截图 |
| 配置 Spider/IPC 执行器资源 | 资源配置页截图、执行器地址、绿色连接状态或日志 |
| 创建 `Wearedge Agent Service` 资源 | 参数截图：`agentHost`、`agentPort`、`apiKeyRef`、`plantId`、`lineId` |
| 配置 `CallWearedgeDecisionApi` Python Function Block | 代码截图、输入端口、JSON 输出端口截图 |
| 使用更新数据表功能块写入全局变量 | 全局数据表变量、绑定关系、运行后数据截图 |
| 配置 Dashboard/ui-builder | 指标卡、决策路径、人工确认、工作流状态截图 |
| 运行并查看日志 | 部署/调试按钮、执行日志、API 返回 JSON 截图 |
| 高风险建议进入人工确认 | pending/approved/rejected 状态截图 |

## 二次开发记忆

自定义资源块需要保留 WFC 的资源包结构。资料中强调资源块目录名、`info.json` 中的 `name`、资源配置里的 `type` 需要保持一致。资源块可打包为 `.zip` 后上传，资料提到 RA API / Swagger UI 入口通常在执行器相关服务的 `:61720/docs`。

后续若要从 runbook 进入可交付资源包，应补齐：

| 文件/目录 | 作用 |
| --- | --- |
| `wfc-blocks/wearedge-agent-service/info.json` | 资源块元数据、参数、资源类型 |
| `wfc-blocks/wearedge-agent-service/README.md` | 安装、参数、截图和边界说明 |
| `wfc-blocks/wearedge-agent-service/function-blocks/CallWearedgeDecisionApi.py` | WFC Python Function Block 示例 |
| `wfc-blocks/wearedge-agent-service/package.ps1` | 生成 `.zip` 的本地打包脚本 |

## 数据表和 ui-builder 记忆

WFC007 的核心模式是：Python Function Block 输出 JSON，将输出端口类型设为 JSON，定义全局数据表变量，再用“更新数据表”功能块绑定变量。ui-builder/HTML 组件可绑定数据流或数据表，对 JSON 里的 `url`、指标和状态做解析展示。

Wearedge 推荐全局数据表最少字段：

| 字段 | 来源 |
| --- | --- |
| `run_id` | Workflow 运行 ID |
| `plant_id` / `line_id` | WFC 资源参数 |
| `primary_direction` | `collaborative_decision.primary_direction` |
| `priority` | `collaborative_decision.priority` |
| `recommendation` | `collaborative_decision.recommendation` |
| `required_confirmations` | `collaborative_decision.required_confirmations` |
| `residual_risk` | `collaborative_decision.residual_risk` |
| `latency_ms` | Wearedge API 响应 |
| `decision_accuracy_pct_estimate` | `competition_metrics.decision_accuracy_pct_estimate` |
| `approval_status` | `pending` / `approved` / `rejected` |
| `evidence_url` | 可选截图、报告或检测图片链接 |

## Spider / IPC 记忆

WFC010 和 WFC002/WFC003 体现的运行链路是：浏览器端工程配置完成后，将 Workflow 部署到 Spider/SPIDR 或 IPC 执行器。资料中的示例包含本地执行器端口 `3002`，云端与本地混合部署时可能需要处理浏览器访问私网地址的限制。赛事 PoC 中应优先形成“部署目标、连接状态、运行日志、停止流程”的四张证据图。

## V3D 仿真记忆

V3D 可作为“柔性生产/换型/状态回放”的演示增强，不是 Phase B 必须项。资料推荐动态模型优先使用 `.gltf`，静态模型可用 `.3mf`，也支持 `.obj`、`.fbx`、`.dae`、`.stl`、`.ply` 等格式。后续如果做仿真证据，应只展示与 Wearedge 决策有关的产线对象：工位、输送线、AGV、机器人、质检点、能耗状态，不做无关视觉装饰。

## 当前仓库对齐结论

| 已具备 | 证据 |
| --- | --- |
| Wearedge WFC API | `POST /v1/workflow-canvas/decision` |
| 本地 smoke test | `scripts/smoke_workflow_canvas_decision.py` |
| API schema | `docs/workflow-canvas-api-schema.md` |
| WFC runbook 初版 | `docs/workflow-canvas-poc-runbook.md` |
| 离线赛事指标验证 | `scripts/run_competition_eval.py`、`docs/competition-offline-eval-report.md` |
| Xcelerator API World 路径 | `docs/xcelerator-apiworld-onboarding.md`、`openapi/wearedge-xcelerator-apiworld.openapi.json` |

## 发现缺口

| 缺口 | 下一步 |
| --- | --- |
| 尚未形成 WFC 资源块目录和 `info.json` | 新增 `wfc-blocks/wearedge-agent-service/` 原型包 |
| 尚未有真实 WFC 登录/Workflow/资源配置截图 | 账号可用后按操作检查清单补截图 |
| 数据表到 ui-builder 的字段绑定尚未截图复现 | 在 WFC 中创建全局数据表并绑定 Dashboard/mock |
| Spider/IPC 部署证据尚未复现 | 使用 PC/NUC 或 IPC 执行器跑一次 smoke workflow |
| V3D 仿真尚未进入证据包 | 可在 Phase C 作为可选增强，不阻塞初版 PoC |

## 下一步优先级

1. 先用 WFC 账号创建项目，复现最小闭环：Python Function Block 调用 Wearedge API，输出 JSON，更新全局数据表。
2. 补一个 WFC 资源块原型包，至少包含 `info.json`、Python 函数示例和 README，便于评审理解二次开发路径。
3. 在 `docs/submission/screenshots-checklist.md` 中增加 WFC 平台截图项，并按真实平台界面逐项打勾。
4. 若 Spider/IPC 条件允许，再补边缘部署截图；若暂时不可用，材料中明确写为“待平台环境复现”。
