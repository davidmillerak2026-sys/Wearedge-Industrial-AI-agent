# Wearedge Industrial Agent Solution Profile

更新日期：2026-06-11

## 解决的工业问题

Wearedge 解决的是多 SKU 离散制造产线中的跨域异常协同决策问题：当设备健康、质量缺陷、能源负荷、订单换型和 Workflow Canvas 工作流状态同时影响生产时，现场团队需要一个低延迟、证据优先、可审批、可回写的决策闭环。

目标场景是汽车零部件、电子装配、包装、食品、医药等频繁换型产线。典型问题不是“问答机器人不够聪明”，而是 MES、QMS、EMS、CMMS、设备信号、视觉证据和一线经验分散，导致根因判断慢、责任边界不清、动作审批和复盘困难。

## 模型接入

当前 PoC 默认模型链路是：

```text
Gemma 4 E2B multimodal GGUF + mmproj
  -> llama.cpp / llama-server
  -> OpenAI-compatible /v1/chat/completions
  -> Wearedge FastAPI gateway
```

默认配置来自 `.env.example`：

| 配置 | 默认值 | 用途 |
| --- | --- | --- |
| `LLAMA_BASE_URL` | `http://127.0.0.1:8080` | 本地 llama-server 地址。 |
| `LLAMA_MODEL` | `gemma4` | 网关传给模型服务的模型名。 |
| `WEAREDGE_MODEL_VARIANT` | `E2B` | 端侧 PoC 模型版本说明。 |
| `WEAREDGE_DEPLOYMENT_MODE` | `local_server` | `jetson` / `ipc` / `local_server` / `cloud_proxy`。 |

模型用于第一视角图片、操作员提示、维修/质量/能耗/换型上下文的理解和解释。模型不直接决定 PLC、机器人、放行、报废、停线、重启、配方变更或能耗策略切换。

## 决策机制

工易魔方主接口 `POST /v1/workflow-canvas/decision` 当前不依赖大模型输出做最终判定，而是使用确定性 KPI 与规则守卫：

```text
selected_directions + context
  -> 每个方向计算 target status / priority / score / evidence
  -> 按 priority 再按 score 选择 primary_direction
  -> 合并 required_confirmations
  -> 生成 Workflow Canvas blocks、数据表字段和 HumanApprovalGate 输入
```

核心实现：

```text
jetson.competition.build_competition_decision()
```

关键指标矩阵：

| Agent 方向 | 决策指标 |
| --- | --- |
| `maintenance` | `f1_pct`、`warning_lead_time_hours`、`root_cause_top3_pct`、`vibration_rms_mm_s` |
| `quality` | `defect_rate_pct`、`detection_confidence_pct`、`relative_improvement_pct` |
| `energy` | `forecast_accuracy_pct`、`saving_pct`、`idle_kw` |
| `flexible_production` | `schedule_efficiency_gain_pct`、`component_reuse_pct`、`target_sku` |
| `workflow_canvas` | `existing_component_use_pct`、`new_component_reuse_potential_pct` |

这套机制的评审口径是：

```text
模型解释证据，确定性规则决定动作边界，工易魔方负责编排、审批和回写。
```

## 平台交付

新增只读接口：

```text
GET /v1/industrial-agent/solution-profile
```

该接口面向 Xcelerator / 工易魔方评审，返回：

- 工业问题和目标客户。
- 端侧部署模式。
- 当前模型和模型角色。
- 多智能体划分。
- KPI 决策矩阵。
- Xcelerator / 工易魔方接入点。
- 离线评估、smoke test 和 live evidence 验证路径。

工易魔方集成仍保持：

```text
Wearedge Agent Service
  -> CallWearedgeDecisionApi
  -> /v1/workflow-canvas/decision
  -> wearedgeDecision data table
  -> Dashboard
  -> HumanApprovalGate
```

## 交付边界

当前可提交的验证是离线/模拟 PoC、端侧 runtime profile、Xcelerator API 草稿、工易魔方接入包、smoke test 和 pytest。真实客户产线数据、真实 SPIDR/IPC 运行日志、正式 Dashboard 和人工确认截图仍按 live evidence checklist 补齐，不能提前写成已完成量产验证。
