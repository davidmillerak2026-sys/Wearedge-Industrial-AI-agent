# 工易魔方 PoC 接入 Runbook

更新日期：2026-06-09

## 目标

在工易魔方中跑通：

```text
读取上下文 -> 调用 Wearedge Agent Service -> 生成协同决策 -> 人工确认 -> 写入数据表 -> Dashboard 展示
```

当前 runbook 用于初赛 PoC 准备。若暂时没有真实工易魔方环境，可先用 `scripts/smoke_workflow_canvas_decision.py` 和 `workflows/wearedge_wfc_poc_payload.json` 验证后端接口。

平台资料对齐记录见 `docs/gongyi-mofang-workflow-canvas-memory-202604.md`。本 runbook 只写可执行闭环，原始资料中的账号激活、资源块打包、Spider/IPC、数据表和 V3D 注意事项统一收敛到该记忆卡。

## 平台准备

| Item | Action | Evidence |
| --- | --- | --- |
| WFC account | 使用 Chrome/Edge 登录 `https://wfc.bd-iiot.com/`，若账号未激活，联系工易魔方团队处理；资料说明激活通常需要 1-2 个工作日。 | 登录页、项目首页或激活沟通记录 |
| Project | 创建 Wearedge 工业智能体 PoC 项目和 Workflow。 | 项目列表、Workflow Canvas 截图 |
| Executor | 绑定 Spider/SPIDR 或 IPC 执行器。资料示例包含本地 `http://<ipc-or-pc-ip>:3002`。 | 执行器地址、连接状态、部署日志 |
| API service | 启动 Wearedge FastAPI 或准备 Xcelerator API World 代理地址。 | `health`/OpenAPI/API Console 截图 |
| Safety | 对高风险建议启用人工确认，不允许模型直接写 PLC/机器人。 | `HumanApprovalGate` 截图 |

## 资源块

自定义资源块：`Wearedge Agent Service`

| Parameter | Example | Purpose |
| --- | --- | --- |
| `agentHost` | `127.0.0.1` | Wearedge FastAPI host or IPC address. |
| `agentPort` | `8081` | Wearedge FastAPI port. |
| `apiKeyRef` | `WEAREDGE_DEMO_TOKEN` | Optional secret reference for bearer token. |
| `deploymentMode` | `jetson` | Edge runtime target: `jetson`, `ipc`, `local_server`, or `cloud_proxy`. |
| `plantId` | `demo-plant-01` | Plant context for data-table filtering. |
| `lineId` | `pkg-line-3` | Production line context. |

资源块二次开发路径：当前仓库已提供原型目录 `wfc-blocks/wearedge-agent-service/`，包含 `info.json`、Python Function Block 示例和本地打包脚本。资源块目录名、`info.json` 中的 `name`、资源配置中的 `type` 需要保持一致；打包为 `.zip` 后可通过资源管理/RA API 上传。

## 功能块

| Block | Input | Output | Notes |
| --- | --- | --- | --- |
| `ReadMesOrder` | order id or line id | target SKU, due date, changeover state | Can read MES table or simulated global data table. |
| `ReadEquipmentSignals` | asset id | vibration, temperature, alarm, maintenance context | Keep numeric units explicit. |
| `ReadQualityData` | lot, station, product | defect rate, detector confidence, quality improvement estimate | Do not let the model invent CTQ limits. |
| `ReadEnergyMeter` | line id, time window | forecast accuracy, saving estimate, idle kW | Require meter baseline before action. |
| `CallWearedgeDecisionApi` | merged JSON context | Wearedge decision JSON | Python Function Block calling REST API. |
| `CollaborativeDecisionGate` | decision JSON | selected recommendation | Implements multi-objective decision display. |
| `HumanApprovalGate` | required confirmations | approved/rejected/pending | Required for high-risk OT actions. |
| `UpdateDashboardDataTable` | decision summary | global table rows | Feeds Dashboard and ui-builder. |

## Python Function Block

Name: `CallWearedgeDecisionApi`

Pseudo-code:

```python
import json
import requests

base_url = f"http://{agentHost}:{agentPort}"
headers = {"Content-Type": "application/json"}
if apiKeyRef:
    headers["Authorization"] = f"Bearer {apiKeyRef}"

payload = {
    "stage": "final",
    "selected_directions": [
        "maintenance",
        "quality",
        "energy",
        "flexible_production",
        "workflow_canvas",
    ],
    "context": {
        "maintenance": equipment_signal_context,
        "quality": quality_context,
        "energy": energy_context,
        "production": mes_order_context,
        "workflow_canvas": workflow_canvas_context,
    },
}

response = requests.post(
    f"{base_url}/v1/workflow-canvas/decision",
    headers=headers,
    data=json.dumps(payload),
    timeout=5,
)
response.raise_for_status()
decision = response.json()
```

输出端口要求：

| Port | Type | Notes |
| --- | --- | --- |
| `decision_json` | JSON | 完整 Wearedge 响应，用于数据表和 Dashboard。 |
| `primary_direction` | string | 便于 WFC 画布直接连线或状态判断。 |
| `requires_human_confirmation` | boolean | 连接人工确认/状态监控功能块。 |
| `error_message` | string | HTTP 超时、401、422、502 或字段缺失时写入。 |

## 全局数据表字段

| Column | Type | Source |
| --- | --- | --- |
| `run_id` | string | Workflow execution id. |
| `plant_id` | string | Resource parameter. |
| `line_id` | string | Resource parameter. |
| `primary_direction` | string | `collaborative_decision.primary_direction` |
| `priority` | string | `collaborative_decision.priority` |
| `recommendation` | string | `collaborative_decision.recommendation` |
| `required_confirmations` | string/list | `collaborative_decision.required_confirmations` |
| `residual_risk` | string | `collaborative_decision.residual_risk` |
| `latency_ms` | number | `latency_ms` |
| `decision_accuracy_pct_estimate` | number | `competition_metrics.decision_accuracy_pct_estimate` |
| `latency_target_met` | boolean | `competition_metrics.latency_target_met` |
| `final_min_agent_directions_met` | boolean | `competition_metrics.final_min_agent_directions_met` |
| `approval_status` | string | `pending`, `approved`, `rejected` |
| `evidence_url` | string | Optional image/report URL for ui-builder HTML display. |

工易魔方资料中的数据表模式是：Python Function Block 输出 JSON，将输出端口类型设为 JSON，定义全局数据表变量，再用“更新数据表”功能块绑定变量。ui-builder 可绑定数据流或数据表，并解析 JSON 字段展示指标、状态或图片链接。

## Dashboard 建议

1. 顶部指标卡：latency、decision accuracy estimate、direction count、target status。
2. 中部决策路径：maintenance、quality、energy、flexible production、workflow canvas 的 status 和 priority。
3. 右侧审批区：required confirmations、residual risk、approval status。
4. 底部证据区：每个方向的 metrics、evidence source、recommendation。

## 演示步骤

1. 启动 Wearedge API。
2. 在工易魔方中绑定 `Wearedge Agent Service`。
3. 准备 MES、设备、质量、能源和 WFC context 表。
4. 运行 `CallWearedgeDecisionApi`。
5. 确认输出包含 `workflow_canvas.function_blocks`、`collaborative_decision`、`competition_metrics`。
6. 将 summary 写入全局数据表。
7. Dashboard 显示指标、建议、确认项和残余风险。
8. 对高风险建议进入 `HumanApprovalGate`，不直接写 PLC。

## WFC 平台截图清单

| Screenshot | Status |
| --- | --- |
| 登录 `https://wfc.bd-iiot.com/` 后的项目首页 | pending |
| Wearedge PoC Workflow Canvas 总览 | pending |
| Spider/SPIDR 或 IPC 执行器资源配置与连接状态 | pending |
| `Wearedge Agent Service` 资源参数 | pending |
| `CallWearedgeDecisionApi` Python Function Block 代码和端口 | pending |
| 全局数据表变量和“更新数据表”绑定 | pending |
| Dashboard/ui-builder 指标卡和决策路径 | pending |
| 工作流部署/调试日志 | pending |
| 人工确认 pending/approved/rejected 状态 | pending |

## V3D 可选增强

若需要展示柔性生产或换型仿真，可使用 V3D 作为 Phase C 演示增强。资料推荐动态模型优先使用 `.gltf`，静态模型可用 `.3mf`，也支持 `.obj`、`.fbx`、`.dae`、`.stl` 等格式。V3D 证据应围绕工位、输送线、AGV、机器人、质检点和能耗状态，不作为离线指标达标依据。

## 本地 Smoke Test

无需启动服务：

```powershell
python scripts/smoke_workflow_canvas_decision.py
```

使用真实 FastAPI 服务：

```powershell
python -m uvicorn jetson.app:app --host 127.0.0.1 --port 8081
python scripts/smoke_workflow_canvas_decision.py --url http://127.0.0.1:8081/v1/workflow-canvas/decision
```

端侧 runtime profile 截图：

```powershell
Invoke-RestMethod http://127.0.0.1:8081/v1/edge/runtime-profile
```

## Xcelerator API World 接入

若通过 Xcelerator API World 发布 Wearedge 服务，优先使用“基于 Xcelerator AppID/Secret 的 X 认证”。API World 代理请求会在请求头携带 `X-TOKEN`，Wearedge 可启用可选验签：

```powershell
$env:WEAREDGE_AUTH_DISABLED="false"
$env:WEAREDGE_XCELERATOR_X_AUTH_ENABLED="true"
$env:WEAREDGE_XCELERATOR_APP_KEY="<Xcelerator AppID>"
python -m uvicorn jetson.app:app --host 0.0.0.0 --port 8081
```

API Console 可导入：

```text
openapi/wearedge-xcelerator-apiworld.openapi.json
```

详细平台字段和截图清单见 `docs/xcelerator-apiworld-onboarding.md`。

## PoC 边界

- 当前 payload 和离线指标是模拟/离线验证数据，不代表客户真实产线数据。
- 高风险控制动作必须经人工确认，不允许由模型或 Python Function Block 直接写入 OT 控制。
- 真实工易魔方环境接入后，需要补充资源块截图、功能块截图、Dashboard 截图和运行日志。
