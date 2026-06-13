# 工易魔方 WFC000-WFC010 手册记忆卡

更新日期：2026-06-13

## 资料范围

本记忆卡来自用户补充的 11 份工易魔方 Workflow Canvas 手册，目的是把临时附件中的操作知识沉淀为 Wearedge 项目长期可复用的工程记忆。不要保存或引用任何账号密码、token、真实密钥。

| 文件 | 项目用途 |
| --- | --- |
| `WFC000_文档列表.docx` | 文档包索引，确认 WFC001-WFC010 各自用途。 |
| `WFC001_工易魔方工作说明书.docx` | WFC 总说明：项目、资源配置、工作流、功能块、数据端口、部署调试、OPC UA、机器人、视觉、AGV、表达式。 |
| `WFC002_蜘蛛执行器使用手册.docx` | PC/NUC 上 Spider 执行器与 WFC 连接路径。 |
| `WFC003_IPC使用手册.docx` | 西门子 Edge IPC 上 Spider 执行器与 WFC 连接路径。 |
| `WFC004_Workflow Canvas Crash Course.docx` | 英文快速课：创建项目、部署、local SPIDR docker、定制资源块/功能块。 |
| `WFC005_如何对资源块及功能块进行二次开发.docx` | 自定义资源块和 Python 功能块二次开发，以 MES REST 服务示例为模板。 |
| `WFC006_资源块安装使用.pdf` | 资源块离线安装：`info.json`、`requirements.txt`、zip、RA API / Swagger。 |
| `WFC007_ 如何保存数据，如何在ui-builder上展示图片.docx` | Python JSON 输出、全局数据表、`更新数据表`、ui-builder/HTML 展示。 |
| `WFC008_V3D支持的格式.docx` | V3D 支持的 3D 模型格式，静态/动态模型选择。 |
| `WFC009_基础方法解释.pdf` | V3D 对象脚本 API、设备绑定、脚本匹配、仿真对象能力。 |
| `WFC010_工易魔方快速入门手册V2.pdf` | 中文快速入门：登录、创建空白项目、拖拽功能块、连接 SPIDR、运行日志、二次开发。 |

## 一句话记忆

WFC 的真实工程路径是：

```text
项目 -> 资源配置 -> 工作流编排 -> Python/功能块代码 -> 数据端口连线 -> 全局数据表 -> ui-builder/Dashboard -> SPIDR/Spider/IPC 部署与日志
```

Wearedge 的 WFC 集成不应被描述成“在 WFC 里训练一个大模型”，而应描述为：把端侧 Wearedge Agent Runtime 封装为 WFC 可配置的 IT 资源服务，再通过 Python Function Block 调用 API，并用 WFC 数据表、Dashboard、调试日志和人工确认形成工业工作流闭环。

## WFC 平台对象

| 对象 | 手册定义 | Wearedge 映射 |
| --- | --- | --- |
| 项目 | 登录后在项目管理页新建、导入、导出、删除项目。 | `Wearedge WFC PoC` 是参赛 PoC 项目。 |
| 资源配置 | 左侧 `编程` -> `配置资源`；资源库可拖拽到资源画布。 | 配置 `通用工控机`/SPIDR 和 `Wearedge Agent Service`。 |
| 通用工控机 / Generic IPC | 在属性面板配置 SPIDR/Spider URL，端口通常为 `3002`；连接成功后状态变绿。 | 证明 WFC 工作流可部署到云端 SPIDR、PC/NUC、IPC 或 Jetson 侧执行器。 |
| 自定义资源 | `用户设备` 下拖入 `自定义资源`，在参数编辑器暴露 IP、端口等参数。 | `Wearedge Agent Service`，参数为 `agentHost`、`agentPort`、`apiKeyRef`、`deploymentMode`、`plantId`、`lineId`。 |
| 工作流画布 | 开始/结束/占位块，拖拽功能块，事件连线表达执行顺序。 | `Start -> CallWearedgeDecisionApi -> UpdateDataTable -> HumanApprovalGate/End`。 |
| 数据端口 | 输入端口接收数据、输出端口输出数据；虚线连接，类型匹配时高亮。 | Python JSON 输出必须连到 `更新数据表` 输入，不能只配置字段。 |
| 右侧面板 | 可显示属性面板、功能块列表/大纲、数据表。 | 取证时优先截图属性面板、大纲视图和数据表。 |
| 部署与调试 | 点击部署/调试后出现运行、更新输入端点、更新输出端点、退出等工具，并显示执行器日志。 | 取证时要拍到 DEBUG 状态、SPIDR URL、运行日志和业务输出。 |
| Dashboard / ui-builder | 可配置轻量看板，也可用 HTML 组件绑定数据流或数据表。 | 展示主方向、优先级、建议动作、指标、残余风险、人工确认状态。 |
| V3D | 轻量 3D 在线/离线仿真，与工作流协同调试。 | 决赛增强柔性生产换型、AGV/输送线/机器人/质检点状态回放。 |

## 最小可执行 WFC 闭环

1. 登录 `https://wfc.bd-iiot.com/`，进入项目管理页。
2. 新建或打开 `Wearedge WFC PoC`。
3. 在 `编程 -> 配置资源` 中配置 `通用工控机` 的 SPIDR/Spider URL。
4. 如果使用本地 Spider/IPC，需要浏览器允许访问本地私网请求，并优先用 WFC 的 http 入口访问本地 `http://<ip>:3002`。
5. 在 `用户设备` 中拖入 `自定义资源`，命名为 `Wearedge Agent Service`。
6. 为 `Wearedge Agent Service` 暴露 `agentHost`、`agentPort`、`apiKeyRef`、`deploymentMode`、`plantId`、`lineId` 参数；`apiKeyRef` 只放引用名，不放真实密钥。
7. 回到工作流画布，拖入 Python 程序块，命名为 `CallWearedgeDecisionApi`。
8. 在 `编辑输入输出` 中将 `input1` 改为 `Resource` 并绑定 `Wearedge Agent Service`，将 `input2` 改为 `JSON` 用于业务上下文，输出端口改为 `JSON`。
9. 双击 Python 程序块，只在业务代码区域写调用 `/v1/workflow-canvas/decision` 的逻辑。
10. 在右侧 `数据表` 新建 Wearedge 决策字段或 JSON 变量。
11. 拖入 `更新数据表` 功能块，绑定目标字段或 JSON 变量。
12. 建立 `CallWearedgeDecisionApi` 的 `输出1` 到 `更新数据表` 输入端口的虚线数据连接。
13. 部署/调试并运行，打开运行日志确认 Python 输出/API 摘要。
14. 工作流运行时不要立即停止，进入 ui-builder/Dashboard 绑定数据表或数据流并预览。

## Wearedge Python Block 模板记忆

WFC005/WFC010 的 MES 示例证明了正确模式：自定义资源暴露 IP/端口，Python Function Block 的 `input1` 绑定该资源，在代码中读取参数后发 REST 请求。

Wearedge 对应实现：

```python
import json
import requests

agent_host = input1["agentHost"]
agent_port = input1["agentPort"]
payload = input2 if isinstance(input2, dict) else json.loads(input2)

headers = {"Content-Type": "application/json"}
url = "http://{}:{}/v1/workflow-canvas/decision".format(agent_host, agent_port)
res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
res.raise_for_status()
result = res.json()
print(json.dumps(result, ensure_ascii=False))
```

现场代码必须以 WFC 生成模板中的变量名为准；如果模板提供 `get_input2()`，优先按模板读取。不要在平台代码里保存真实 API key。

## 数据表与 ui-builder 关键记忆

WFC007 对 Wearedge 最关键：只创建数据表字段和 `更新数据表` 绑定还不等于写回完成，必须建立 Python 输出端口到 `更新数据表` 输入端口的虚线数据线。

Wearedge 数据表最小字段：

| 字段 | 含义 |
| --- | --- |
| `selected_direction` | 主方向，如 maintenance / quality / energy / scheduling。 |
| `priority` | 协同决策优先级。 |
| `recommended_action` | 建议动作或检查步骤。 |
| `evidence_summary` | 证据摘要。 |
| `competition_metrics` | 赛事指标摘要。 |
| `owner` | 责任角色。 |
| `residual_risk` | 残余风险。 |
| `approval_status` | `pending` / `approved` / `rejected`。 |

ui-builder 展示路径：

1. 运行工作流后保持实例运行。
2. 打开 ui-builder 或 Dashboard 预览入口。
3. 拖入 HTML/卡片组件。
4. 绑定数据流数据源，获取数据表。
5. 在 WFC `工具 -> 项目&工作流常量` 中查看 workflow instance ID 等常量。
6. 先 `try` 验证能取到数据，再预览。
7. 如果 JSON 中有图片或证据 URL，可在 HTML 组件中解析并展示。

## Spider / IPC 端侧执行器记忆

WFC002/WFC003/WFC010 均确认端侧执行器路径：

| 场景 | 操作要点 | Wearedge 证据 |
| --- | --- | --- |
| 云端 SPIDR | `通用工控机` URL 使用云端 SPIDR 地址，状态变绿后可部署。 | 平台 DEBUG 和运行日志证据。 |
| PC/NUC Spider | 设备上已安装 Spider，电脑与设备在同一网络；在 WFC 中填 `http://<设备IP>:3002`。 | 本地边缘执行器连接截图。 |
| IPC Spider | IPC 上电、接网线、获取 IP；WFC 填 `http://<IPC IP>:3002`；可浏览器访问该地址查看状态。 | IPC 端侧运行证据。 |
| 本地私网限制 | Chrome 需关闭私网请求阻断；https 页面可能访问不了本地 http Spider。 | 失败时不要误判为 Wearedge API 故障。 |

对 Wearedge 来说，Jetson 也应按“端侧节点 + 本地服务 + WFC 资源配置”的思路处理：在 Jetson 上另建 Wearedge 项目目录，启动 Agent Runtime/API，再让 WFC 的 Python Block 调用它。不要混入 Jetson 上已有的其他项目目录。

## 资源块标准化入库记忆

WFC006/WFC005 给出从“画布快速配置”升级到“标准库组件”的路径：

1. 准备资源块目录。
2. 添加 `info.json`，其中 `name` 必须与资源块文件夹名一致。
3. `type` 要匹配 WFC 资源配置页中的资源 ID。
4. 添加 `requirements.txt` 描述 Python 依赖。
5. 只打包必要文件为 `.zip`，控制资源块体积。
6. 通过 RA API 上传，Swagger UI 入口通常是 `:61720/docs`。
7. 回到资源配置页添加资源并配置参数。
8. 在工作流页添加功能块并引用该资源。

Wearedge 后续可交付：

| 目录/文件 | 用途 |
| --- | --- |
| `wfc-blocks/wearedge-agent-service/info.json` | `Wearedge Agent Service` 资源块元数据。 |
| `wfc-blocks/wearedge-agent-service/requirements.txt` | Python 依赖边界。 |
| `wfc-blocks/wearedge-agent-service/function-blocks/CallWearedgeDecisionApi.py` | 可复用功能块示例。 |
| `wfc-blocks/wearedge-agent-service/README.md` | 安装、参数、截图、风险边界。 |
| `wfc-blocks/wearedge-agent-service/package.ps1` | 生成 zip 包。 |

## 功能块与安全边界

WFC001 支持 OPC UA 读写变量、机器人运动、夹爪、相机、AGV、状态监控、并行、循环、子工作流等功能。Wearedge 参赛材料中可以展示它具备从 IT 决策走向 OT 闭环的能力，但初赛 PoC 不应让 AI 自动写 PLC、机器人或质量放行。

推荐边界：

| 类型 | 初赛做法 |
| --- | --- |
| OPC UA 读变量 | 可作为上下文读取或模拟证据。 |
| OPC UA 写变量 | 高风险，必须经过 `HumanApprovalGate`，初赛默认不自动写真实 OT。 |
| 机器人/AGV 控制 | 可用 WFC/V3D/离线仿真展示，不直接让模型下发动作。 |
| 质量放行 | 模型只给建议和证据，最终人工确认。 |
| 能源/调度参数 | 可先写数据表和 Dashboard，真实控制动作留作决赛 PoC。 |

## V3D 仿真记忆

WFC008/WFC009 可用于决赛增强，不阻塞当前初赛提交。

| 项 | 记忆 |
| --- | --- |
| 推荐格式 | 动态模型优先 `.gltf`，静态模型优先 `.3mf`；也支持 `.obj`、`.fbx`、`.dae`、`.stl`、`.ply` 等。 |
| 设备绑定 | 场景对象的 `resource` 值要与资源块中的设备 ID 匹配。 |
| 脚本匹配 | 功能块 ID 需去掉数字编号后匹配脚本名。 |
| 典型对象 | Conveyor、Elevator、AGV、Camera、Sensor、Robot、Endeffector、Curve。 |
| Wearedge 用法 | 展示订单变化、换型、质检点异常、设备风险、能源状态和人工确认后的产线状态回放。 |

## 对当前 live WFC 证据的解释边界

已有真实 WFC 页面证据显示：

- `CallWearedgeDecisionApi` Python Block 已存在。
- 自定义数据表字段已存在。
- `System.UpdateDataTable - 更新数据表.1` 已被创建。
- `更新数据表.1` 已绑定 `selected_direction`、`priority`、`recommended_action`、`approval_status` 等字段。
- DEBUG 状态下可看到 WFC 运行工具条、SPIDR URL、`更新数据表` 属性面板和运行日志窗口。

仍不能夸大为：

- Python 输出已经原生写回数据表。
- WFC 原生日志已经显示 `ok=true`、`latency_ms` 或业务 JSON。
- Dashboard 已经完成 Wearedge 数据绑定。
- 真实 OT 设备已经被 Wearedge 自动控制。

下一步 GUI 取证优先级：

1. 在 WFC 画布中稳定建立 `CallWearedgeDecisionApi 输出1 -> 更新数据表 输入` 虚线数据连接。
2. 运行 DEBUG，打开运行日志，争取看到 Python 输出或 API 摘要。
3. 切到 `数据表`，截取运行后字段值。
4. 保持工作流运行，进入 ui-builder/Dashboard，绑定数据源并预览。
5. 形成 `05-run-log-ok-true.png`、`04-dashboard-decision-view.png`、`06-human-approval-gate.png` 的真实替代证据。

## 夺冠叙事强化

这批手册进一步支撑 Wearedge 的核心表达：

```text
工易魔方负责编排、部署、调试、数据表、看板和 OT 工作流安全边界；
Wearedge 负责端侧多智能体协同决策、工业 RAG、确定性守卫和结构化证据输出；
两者结合后，才能把“单点 AI API”升级为“可部署、可审计、可人工确认、可逐步连到产线的工业智能体工作流”。
```

提交材料中的关键词应固定为：端侧智能体运行时、WFC 自定义资源、Python Function Block、SPIDR/Spider/IPC、全局数据表、ui-builder/Dashboard、HumanApprovalGate、离线/仿真 PoC、真实 OT 动作需人工确认。
