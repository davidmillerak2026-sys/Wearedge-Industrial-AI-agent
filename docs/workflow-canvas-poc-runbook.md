# 工易魔方 PoC 接入 Runbook

更新日期：2026-06-04

## 目标

在工易魔方中跑通：

```text
读取上下文 -> 调用 Wearedge Agent Service -> 生成协同决策 -> 人工确认 -> 写入数据表 -> Dashboard 展示
```

当前 runbook 用于初赛 PoC 准备。若暂时没有真实工易魔方环境，可先用 `scripts/smoke_workflow_canvas_decision.py` 和 `workflows/wearedge_wfc_poc_payload.json` 验证后端接口。

## 资源块

自定义资源块：`Wearedge Agent Service`

| Parameter | Example | Purpose |
| --- | --- | --- |
| `agentHost` | `127.0.0.1` | Wearedge FastAPI host or IPC address. |
| `agentPort` | `8081` | Wearedge FastAPI port. |
| `apiKeyRef` | `WEAREDGE_DEMO_TOKEN` | Optional secret reference for bearer token. |
| `plantId` | `demo-plant-01` | Plant context for data-table filtering. |
| `lineId` | `pkg-line-3` | Production line context. |

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

## PoC 边界

- 当前 payload 和离线指标是模拟/离线验证数据，不代表客户真实产线数据。
- 高风险控制动作必须经人工确认，不允许由模型或 Python Function Block 直接写入 OT 控制。
- 真实工易魔方环境接入后，需要补充资源块截图、功能块截图、Dashboard 截图和运行日志。
