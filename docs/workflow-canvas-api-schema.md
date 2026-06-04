# Workflow Canvas Decision API Schema

更新日期：2026-06-04

## Endpoint

`POST /v1/workflow-canvas/decision`

同等本地验证入口：`POST /v1/competition/decision`

用途：供工易魔方 Python Function Block 调用 Wearedge 多智能体协同决策服务，并将输出写入全局数据表、Dashboard 和人工审批节点。

## Request JSON

```json
{
  "stage": "final",
  "selected_directions": [
    "maintenance",
    "quality",
    "energy",
    "flexible_production",
    "workflow_canvas"
  ],
  "context": {
    "maintenance": {
      "f1_pct": 88.0,
      "warning_lead_time_hours": 30.0,
      "root_cause_top3_pct": 92.0,
      "vibration_rms_mm_s": 7.2,
      "has_threshold_evidence": true
    },
    "quality": {
      "defect_rate_pct": 3.4,
      "detection_confidence_pct": 93.0,
      "relative_improvement_pct": 6.0,
      "has_detector_evidence": true
    },
    "energy": {
      "forecast_accuracy_pct": 96.0,
      "saving_pct": 12.0,
      "idle_kw": 5.8,
      "has_meter_baseline": true
    },
    "production": {
      "schedule_efficiency_gain_pct": 22.0,
      "component_reuse_pct": 76.0,
      "target_sku": "SKU-C500",
      "has_released_checklist": true
    },
    "workflow_canvas": {
      "existing_component_use_pct": 72.0,
      "new_component_reuse_potential_pct": 80.0
    }
  }
}
```

## Required Top-Level Fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `stage` | string | no | `initial` or `final`; defaults to `initial` when missing. |
| `selected_directions` | string array | no | Defaults to maintenance, quality, flexible production, and Workflow Canvas. |
| `context` | object | no | Context tables from MES, quality, energy, maintenance, and WFC blocks. |

## Direction Aliases

| Input | Normalized Direction |
| --- | --- |
| `iqc`, `quality_agent`, `quality_control` | `quality` |
| `energy_agent`, `energy_management`, `power_management` | `energy` |
| `maintenance_agent`, `predictive_maintenance`, `equipment_maintenance` | `maintenance` |
| `changeover`, `production`, `flexible_manufacturing` | `flexible_production` |
| `wfc`, `workflow`, `gongyi_mofang` | `workflow_canvas` |

## Response JSON

Important response fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `ok` | boolean | Decision service completed. |
| `version` | string | Decision payload version. |
| `stage` | string | Evaluation stage. |
| `selected_directions` | string array | Normalized directions used by the evaluator. |
| `latency_ms` | integer | Server-side decision latency. |
| `competition_targets` | object | Current competition target constants. |
| `competition_metrics` | object | Latency, direction-count, and decision-accuracy target checks. |
| `compliance` | object | Initial/final round readiness checks. |
| `evaluations` | object array | Per-direction status, priority, metrics, evidence, recommendation, confirmations, and workflow blocks. |
| `collaborative_decision` | object | Primary direction, priority, recommendation, human confirmation state, and residual risk. |
| `workflow_canvas` | object | Resource block, function blocks, data table update payload, and Python Function Block call metadata. |

## Data Table Mapping

| Data Table Column | Source Field |
| --- | --- |
| `primary_direction` | `collaborative_decision.primary_direction` |
| `priority` | `collaborative_decision.priority` |
| `recommendation` | `collaborative_decision.recommendation` |
| `requires_human_confirmation` | `collaborative_decision.requires_human_confirmation` |
| `required_confirmations` | `collaborative_decision.required_confirmations` |
| `residual_risk` | `collaborative_decision.residual_risk` |
| `latency_ms` | `latency_ms` |
| `decision_accuracy_pct_estimate` | `competition_metrics.decision_accuracy_pct_estimate` |
| `latency_target_met` | `competition_metrics.latency_target_met` |
| `final_min_agent_directions_met` | `competition_metrics.final_min_agent_directions_met` |
| `workflow_function_blocks` | `workflow_canvas.function_blocks` |

## Dashboard Mapping

| Dashboard Area | Suggested Fields |
| --- | --- |
| Metric cards | latency, decision accuracy estimate, direction count, target status |
| Decision path | selected directions, primary direction, per-direction status |
| Human approval | required confirmations, residual risk, responsible role |
| Work order / QMS / EMS preview | per-direction recommendation and evidence source |
| Workflow status | resource block, function blocks, data table update status |

## Error Handling

- If gateway auth is enabled, include `Authorization: Bearer <DEMO_TOKEN>`.
- If HTTP status is `401`, check `apiKeyRef` or token binding.
- If HTTP status is `422`, check the Python Function Block request body is a JSON object.
- If `ok` is not true or required response fields are missing, route to `HumanApprovalGate` and show the raw response in the Dashboard.

## Smoke Test

```powershell
python scripts/smoke_workflow_canvas_decision.py
```

For a running gateway:

```powershell
python scripts/smoke_workflow_canvas_decision.py --url http://127.0.0.1:8081/v1/workflow-canvas/decision
```
