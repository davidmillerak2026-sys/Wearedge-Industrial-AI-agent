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

官方资料到可执行路径的最新决策表见 `docs/gongyi-mofang-official-completion-paths.md`。结论是：当前没有确认的官方 CLI 可完整编辑 WFC 项目；官方主路径仍是 WFC 项目、资源配置、Python 程序块、全局数据表、Dashboard/ui-builder 和 Spider/SPIDR 日志。CLI/API 只作为打包、只读探测、备份和 smoke test 辅助，不替代 live WFC 运行证据。

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
| 已形成 WFC 资源块目录和 `info.json` | 后续在真实 WFC 平台上传/截图复现 |
| 尚未有真实 WFC 登录/Workflow/资源配置截图 | 账号可用后按操作检查清单补截图 |
| 数据表到 ui-builder 的字段绑定尚未截图复现 | 在 WFC 中创建全局数据表并绑定 Dashboard/mock |
| Spider/IPC 部署证据尚未复现 | 使用 PC/NUC 或 IPC 执行器跑一次 smoke workflow |
| V3D 仿真尚未进入证据包 | 可在 Phase C 作为可选增强，不阻塞初版 PoC |

## 下一步优先级

1. 先用 WFC 账号创建项目，复现最小闭环：Python Function Block 调用 Wearedge API，输出 JSON，更新全局数据表。
2. 补一个 WFC 资源块原型包，至少包含 `info.json`、Python 函数示例和 README，便于评审理解二次开发路径。
3. 在 `docs/submission/screenshots-checklist.md` 中增加 WFC 平台截图项，并按真实平台界面逐项打勾。
4. 若 Spider/IPC 条件允许，再补边缘部署截图；若暂时不可用，材料中明确写为“待平台环境复现”。

## 2026-06-09 操作级补充记忆

本节来自对工易魔方资料包、WFC001-WFC010 技术文档、资源块安装文档、Spider/IPC 手册和当前 live WFC 页面试操作的重新回顾。后续不要再靠盲点试错，应按以下操作模型执行。

### 正确心智模型

工易魔方的核心链路不是“在网页里写一个 AI 应用”，而是：

```text
项目 -> 资源配置 -> 工作流编排 -> Python/功能块业务代码 -> 全局数据表 -> Dashboard/ui-builder -> 部署到 Spider/IPC -> 日志/调试
```

对 Wearedge 而言，应区分三类对象：

| 对象 | WFC 角色 | Wearedge 口径 |
| --- | --- | --- |
| `通用工控机` / `Generic IPC` | Spider/SPIDR 执行器连接点，通常配置 `http://端侧IP:3002` 或云端 SPIDR URL | 证明工作流可部署到端侧/IPC/本地执行器 |
| `自定义资源` / `Custom Resource` | 暴露 IT 服务或设备参数，如 IP、端口、业务参数 | 表示 `Wearedge Agent Service` 的 host、port、plant、line 等参数 |
| `Python 程序块` / Python Block | 写业务代码、调用 REST API、绑定资源和 JSON 输入输出 | 实现 `CallWearedgeDecisionApi`，POST `/v1/workflow-canvas/decision` |

不能把 `通用工控机` 和 `Wearedge Agent Service` 混成一个资源。前者是 WFC 工作流运行时，后者是被 Python Block 调用的边缘智能体服务。

### 项目与主界面入口

| 目标 | 手册入口 | 操作记忆 |
| --- | --- | --- |
| 登录 | `https://wfc.bd-iiot.com/` | 推荐 Chrome/Edge；注册后需激活；登录后进入项目管理页。 |
| 新建项目 | 项目管理页 -> `新建空白项目` | 填项目名和描述，创建后点击项目卡进入编辑器。 |
| 工作流编辑 | 默认进入项目后的 `工作流.1` | 左侧有 `画布` / `编程`，画布中默认 `开始`、`结束` 或 `占位`。 |
| 资源配置 | 左侧 `编程` -> `配置资源`，或项目中的 `Resource` tab | 左侧是资源库，中间是资源画布，右侧是资源树/属性面板。 |
| 功能块库 | 左侧 `编程` | 展开 `资源列表`、`通用`、`控制流`、`编程语言` 等分类。 |
| 右侧面板 | 画布右侧展开箭头 | 可切 `属性面板`、`大纲视图`、`数据表`。 |
| 运行调试 | 右上部署/运行图标 | 部署后可查看日志、运行、退出；画布下方或右侧显示执行器日志。 |

### 资源配置正确路径

配置端侧执行器：

1. 进入 `编程` -> `配置资源`。
2. 选择或保留 `通用工控机`。
3. 在属性面板中设置 Spider/SPIDR URL，常见格式是 `http://<IPC或本地设备IP>:3002`。
4. 如果页面有 `存在执行器`，设置为 `是`。
5. 连接成功时，资源块左上角小圆点或底部状态条会变绿。
6. 如果使用本地私网 Spider，手册要求浏览器关闭 `Block insecure private network requests`，并优先使用 http 版 WFC 地址，否则 https 页面可能访问不了本地 `http://<ip>:3002`。

配置 `Wearedge Agent Service` 自定义资源：

1. 进入 `编程` -> `配置资源`。
2. 展开 `用户设备`。
3. 拖入 `自定义资源`。
4. 改名为 `Wearedge Agent Service`。
5. 在右侧属性面板中编辑参数。
6. 最少参数建议：

| 参数 ID | 显示名 | 类型 | 默认/说明 |
| --- | --- | --- | --- |
| `agentHost` | Agent Host | String | 本地 API 主机，如 `127.0.0.1` 或边缘节点 IP |
| `agentPort` | Agent Port | Number | 默认 `8000` |
| `apiKeyRef` | API Key Ref | String | 只填引用名，不填真实密钥 |
| `deploymentMode` | Deployment Mode | String | `jetson` / `ipc` / `local_server` / `cloud_proxy` |
| `plantId` | Plant ID | String | 示例 `demo-plant-a` |
| `lineId` | Line ID | String | 示例 `line-flex-01` |

### Python Function Block 正确路径

手册给了两种可用方式：`通用` 下的 `自定义功能块`，或 `编程语言` 下的 Python 程序块。Wearedge 优先使用 Python 程序块，因为它最适合调用 HTTP API。

1. 回到工作流画布。
2. 左侧切 `编程`。
3. 展开 `编程语言`。
4. 拖入 `Python` 程序块到 `占位`，或拖到开始/结束之间。
5. 在属性面板中改名为 `CallWearedgeDecisionApi`。
6. 点击 `编辑输入输出`。
7. 将 `input1` 类型改为 `Resource`，绑定 `Wearedge Agent Service`。
8. 将 `input2` 类型改为 `JSON`，用于传入 WFC context payload。
9. 将输出端口类型改为 `JSON`。
10. 双击 Python Block 打开代码模板。
11. 只在 `-- Business Code Start --` 到 `Business Code End` 之间写业务代码。
12. 保存时使用代码编辑器里的 `Save All and Close` 或等价按钮。

Wearedge Python Block 代码形态：

```python
import json
import requests

agent_host = input1["agentHost"]
agent_port = input1["agentPort"]
payload = input2 if isinstance(input2, dict) else json.loads(input2)

url = "http://{}:{}/v1/workflow-canvas/decision".format(agent_host, agent_port)
headers = {"Content-Type": "application/json"}
res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
res.raise_for_status()
result = res.json()
print(json.dumps(result, ensure_ascii=False))
```

现场实现时以 WFC 自动生成的变量名为准。如果模板提供 `get_input2()`，则使用模板函数读取 JSON 输入。不要在平台中写真实 API key。

### 数据表和 Dashboard 正确路径

全局数据表：

1. 打开右侧 `数据表` tab。
2. 点击右侧 `编辑`。
3. 新建变量，建议先建一个 JSON 变量，如 `wearedgeDecision`，再按需拆字段。
4. 拖入 `通用` 下的 `更新数据表` 功能块。
5. 在 `更新数据表` 的属性面板中绑定 `wearedgeDecision`。
6. 将 `CallWearedgeDecisionApi` 的 JSON 输出连到 `更新数据表` 输入。
7. 运行后截图：变量定义、绑定关系、运行后的 JSON 值。

建议字段：

| 字段 | 映射 |
| --- | --- |
| `primary_direction` | `collaborative_decision.primary_direction` |
| `priority` | `collaborative_decision.priority` |
| `recommendation` | `collaborative_decision.recommendation` |
| `required_confirmations` | `collaborative_decision.required_confirmations` |
| `residual_risk` | `collaborative_decision.residual_risk` |
| `latency_ms` | `latency_ms` 或 `competition_metrics.latency_ms` |
| `approval_status` | 初始 `pending`，人工确认后更新 |

Dashboard/ui-builder：

1. 先运行工作流，不要停止。
2. 打开 ui-builder / Dashboard。
3. 拖入 HTML 或卡片组件。
4. 绑定数据流或数据表。
5. `工具` -> `项目&工作流常量` 可查看 workflow instance ID 等常量。
6. 解析 `wearedgeDecision` JSON，展示主方向、建议动作、指标、确认项和残余风险。
7. 如果 JSON 里有 `url`，可按 WFC007 示例生成 `<img>` 展示证据图。

### 部署与日志正确路径

1. 保存资源配置和工作流。
2. 点击右上角部署/调试按钮。
3. 选择部署。
4. 查看运行日志。
5. 点击运行。
6. 截图日志中 Python Block 的 `print` 输出或 API 返回摘要。
7. 退出部署后再继续编辑。

赛事证据中需要说明：

- 若 Spider/IPC 未绿色连接，则这是“平台编辑态证据”，不能写成已完成端侧执行。
- 若连接本地 Spider/IPC 成功，则这是“端侧工作流运行证据”，应作为 Wearedge 端侧优势重点。

### 标准化资源块/功能块入库路径

如果从“画布内快速定义”升级为“标准库组件”：

1. 使用开发者工坊 / Foundry。
2. 创建资源块或功能块。
3. 定义参数。
4. 修改元信息和 UI 信息，包括 ID、语言、资源名称、描述、标题、颜色、图标。
5. 点击 `更新到库`。
6. 回到资源配置或功能块库，在 `用户设备` / `用户功能块库` 中拖拽使用。

离线包安装路径：

1. 资源块目录名、`info.json.name` 和资源配置 `type` 必须匹配。
2. 加入 `requirements.txt` 描述 Python 依赖。
3. 只打包必要文件为 `.zip`。
4. 通过 RA API / Swagger UI 上传，手册提到入口通常为 `:61720/docs`。
5. 在资源配置页添加对应资源并配置参数。
6. 在工作流页添加功能块并引用该资源。

### V3D 记忆

V3D 是可选增强项，不阻塞当前 live evidence。其价值是展示柔性生产、换型、AGV/机器人/输送线/质检点的状态回放。

| 用途 | 推荐格式/方法 |
| --- | --- |
| 动态模型 | `.gltf` 优先 |
| 静态模型 | `.3mf` 优先，也可 `.obj`、`.stl`、`.ply` |
| 设备绑定 | 场景中设备对象的 `resource` 与资源块 ID 匹配 |
| 脚本匹配 | 去除功能块 ID 的数字编号后与脚本名匹配 |
| 仿真对象能力 | 输送线、升降机、AGV、相机、传感器、末端执行器、机器人等基础方法 |

### Wearedge live evidence 路线

后续平台截图优先按以下顺序补，不再从界面上随机寻找：

| 顺序 | 证据文件 | 必须拍到 |
| --- | --- | --- |
| 1 | `00-wfc-projects-authenticated.png` | 已登录项目页 |
| 2 | `08-wfc-project-created-card.png` | `Wearedge WFC PoC` 项目卡 |
| 3 | `09-wfc-project-editor-opened.png` | 项目进入编辑器 |
| 4 | `01-resource-block-wearedge-agent-service.png` | 资源配置页，自定义资源或通用工控机连接参数 |
| 5 | `02-python-function-block-call-api.png` | Python Block 名称、输入输出或代码编辑器 |
| 6 | `03-global-data-table-decision-fields.png` | 右侧数据表变量和 `更新数据表` 绑定 |
| 7 | `04-dashboard-decision-view.png` | Dashboard/ui-builder 展示 JSON 决策 |
| 8 | `05-run-log-ok-true.png` | 部署/运行日志、API 返回摘要 |
| 9 | `06-human-approval-gate.png` | pending/approved/rejected 或人工确认状态 |

### 当前自动化经验

WFC 很多核心元素是 canvas 绘制，DOM 里不一定能看到块名、端口和右键菜单。后续浏览器操作策略：

1. 先按文档锁定入口，再操作。
2. 对 canvas 元素用截图确认，少用 DOM 文本猜测。
3. 每一步先截图再继续，避免操作成功但证据丢失。
4. 创建、上传、发布、保存密钥、写企业敏感信息前必须确认授权。
5. 本项目不得保存 WFC 密码、token、真实 API key。
6. 不发布上架，不向真实 OT 输出写控制指令。

### 2026-06-09 live WFC 实操状态

本节记录已经在真实 WFC 项目中发生的状态，用于后续继续补证据：

| 项目 | 当前状态 | 证据/备注 |
| --- | --- | --- |
| 项目 | `Wearedge WFC PoC` 已创建并进入编辑器 | `00`、`07`、`08`、`09` 系列截图。 |
| 自定义资源 | `Wearedge Agent Service` 已创建，已保存 `agentHost / Agent Host` 参数 | `01-resource-block-wearedge-agent-service.png`、`47-wfc-agent-host-param-confirmed.png`。 |
| 资源参数缺口 | `agentPort`、`apiKeyRef`、`deploymentMode`、`plantId`、`lineId` 尚未稳定补入平台参数编辑器 | 不能在材料里写成已完成。 |
| Python 程序块 | `编程` 库搜索 `Python` 成功，能看到 `编程语言` 分类和 Python 程序块入口；2026-06-11 已拖入画布并保存。 | `59-wfc-python-search.png`、`79-wfc-python-search-filled.png`、`81-wfc-python-drag-center-attempt.png`。 |
| Python 拖拽/命名 | 已形成可确认的新块并在属性面板命名为 `CallWearedgeDecisionApi`，源码编辑器 `fb_main.py` 可打开。 | `02-python-function-block-call-api.png`、`86-wfc-python-block-renamed-code-dialog.png`。 |
| Python 源码参考 | live WFC `fb_main.py` 已复核为 Wearedge 摘要版本 | `workflows/wfc_call_wearedge_decision_fb_main.py`，调用 `/v1/workflow-canvas/decision`，记录 `wearedge_decision_ok`，不包含账号、token 或密钥；2026-06-12 平台源码搜索截图 `103-wfc-python-fb-main-search-state.png` 可见 `_summary`、`selected_direction`、`approval_status`。 |
| 数据表 | 右侧 `数据表` tab 可进入；2026-06-12 已在真实 WFC 项目 `编辑数据表 -> 自定义数据` 中复核 8 个 Wearedge 决策字段。 | `03-global-data-table-decision-fields.png` 已显示主方向、优先级、建议动作、证据摘要、指标、责任人、残余风险、人工确认状态。 |
| Dashboard | 已进入 `/dashboard-explorer` | `71-wfc-dashboard-explorer-entry-native.png` 只是入口图，不是 Wearedge Dashboard 完成图。 |
| 运行日志 | 2026-06-11 已进入 `DEBUG` 状态，执行器显示 `https://spidr.wfc.bd-iiot.com`；运行日志 iframe 可打开并读取到 `Workflow is ready.`。 | `95-wfc-debug-state-spidr-open.png`、`96-wfc-run-log-workflow-ready.png/json` 是辅助证据；还不能命名为 `05-run-log-ok-true.png`，因为 Python Block 尚未形成 `ok=true` API 调用日志。 |
| 截图方法 | 默认 Browser 截图在 WFC canvas 页面可能超时或只截左侧画布；右侧弹窗字段可通过实时 DOM 核验。 | 最终材料优先使用清晰平台图；若截图工具裁剪，使用明确标注的 DOM verified evidence，不伪装为原生截图。 |

2026-06-11 Dashboard Explorer 路由分析：

2026-06-11 源码编辑补充：

- WFC 处于 `DEBUG` 时 `fb_main.py` 编辑器为只读，会提示 `Cannot edit in read-only editor`。
- 需要先点击调试浮条 stop 图标，使顶部恢复 `已保存` / `play-circle` 状态，再打开源码编辑器粘贴保存。
- 若需要平台内业务 `ok=true` 运行日志或数据表写回，下一步应在现有 `CallWearedgeDecisionApi` 后增加/绑定 `更新数据表` 或打开 read 输出，让 `ok`、`latency_ms`、`selected_direction`、`approval_status` 可见；当前已取得 WFC 原生 `状态码 Good` 运行态。

| 发现 | 结论 |
| --- | --- |
| `/dashboard-explorer` 页面显示 `No Dashboard`。 | 当前租户/项目没有可预览 Dashboard，空页不是创建入口。 |
| 前端代码读取 `/api/projects/dashboard-explorer`。 | Dashboard Explorer 是列表/预览页，依赖后台已有 Dashboard 记录。 |
| 有 Dashboard 时通过 `/remote/preview?_wfc=...&_projectid=...&_token=...&_spidr=...&_projectInstanceId=...` 加载。 | 真正 Dashboard 证据需要先有 workflow instance / ui-builder 应用，再从预览 URL 截图。 |
| 直接访问 `/edit/apps` 会回到项目页。 | 不能把 `/edit/apps` 当成稳定创建入口；下一步应按 WFC007 路线：运行工作流 -> 不停止实例 -> 从 ui-builder 绑定数据表/数据流 -> 再预览。 |

2026-06-11 已创建的 WFC 自定义数据字段：

| 字段 ID | 显示名 | 用途 |
| --- | --- | --- |
| `selected_direction` | 主方向 selected_direction | 主智能体/主优化方向 |
| `priority` | 优先级 priority | 决策优先级 |
| `recommended_action` | 建议动作 recommended_action | 推荐执行或检查动作 |
| `evidence_summary` | 证据摘要 evidence_summary | 证据来源和关键依据 |
| `competition_metrics` | 指标 competition_metrics | 赛事指标和估算结果 |
| `owner` | 责任人 owner | 责任角色或处理人 |
| `residual_risk` | 残余风险 residual_risk | 人工确认前的残余风险 |
| `approval_status` | 人工确认状态 approval_status | `pending` / `approved` / `rejected` |

### 夺冠叙事对应

工易魔方材料强调低代码、IT/OT 融合、Spider/IPC 边缘执行器、AI/算法封装、Dashboard、柔性生产和生态共创。Wearedge 的最佳表达应固定为：

```text
Wearedge Agent Runtime 部署在 Jetson / IPC / 本地工控机等端侧算力，
工易魔方通过自定义资源和 Python Function Block 调用它，
再将协同决策结果写入全局数据表、Dashboard 和人工确认流程。
模型只做解释、建议和指标推断，动作边界由确定性守卫、WFC 工作流和人工确认控制。
```
