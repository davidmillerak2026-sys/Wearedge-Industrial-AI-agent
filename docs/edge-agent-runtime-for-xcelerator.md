# Edge Agent Runtime for Xcelerator and Gongyi Mofang

更新日期：2026-06-09

## 一句话定位

Wearedge 的核心优势是把工业智能体运行时部署到端侧算力里，再由 Siemens Xcelerator / 工易魔方完成平台编排、人工确认和数据回写。端侧节点可以是 Jetson、Siemens Edge IPC、本地工控机或产线边缘服务器。

```text
M400 / AR / Camera / OPC UA / MES / QMS / EMS / CMMS
  -> Wearedge Edge Agent Runtime on Jetson / IPC / local server
  -> local multimodal inference + RAG + deterministic guards + audit
  -> Xcelerator API World / Gongyi Mofang Workflow Canvas
  -> global data table + Dashboard + HumanApprovalGate
```

## Why This Wins Enterprise Group

| Advantage | Evidence |
| --- | --- |
| 数据不出厂 | 图片、设备上下文、知识库和审计日志可留在边缘节点。 |
| 低延迟协同决策 | `/v1/workflow-canvas/decision` 当前离线 smoke 可在毫秒级返回决策结构。 |
| 可穿戴一线入口 | M400 / AR 第一视角把现场工人纳入智能体闭环。 |
| 工易魔方可编排 | WFC Python Function Block 调用 Wearedge API，结果写入全局数据表和 Dashboard。 |
| 企业安全边界 | 高风险动作进入 `HumanApprovalGate`，模型不直接写 PLC、停线或质量放行。 |
| 可共创产品化 | `wfc-blocks/wearedge-agent-service/` 给出资源块原型，便于西门子专家审阅共创路径。 |

## Public Runtime Profile

新增只读接口：

```text
GET /v1/edge/runtime-profile
```

用途：

- 给 Xcelerator / 工易魔方评审展示当前部署形态。
- 展示端侧能力：本地多模态推理、工作流决策、审计日志、WFC-ready、安全边界。
- 作为视频和截图证据，证明 Wearedge 不是云端 Chatbot，而是可部署在产线边缘节点的 Agent Runtime。

本地验证：

```powershell
python -m uvicorn jetson.app:app --host 127.0.0.1 --port 8081
Invoke-RestMethod http://127.0.0.1:8081/v1/edge/runtime-profile
```

## Deployment Modes

| Mode | Meaning | Best Use |
| --- | --- | --- |
| `jetson` | Jetson Orin Nano / Orin class edge AI node | M400/AR local multimodal inference, data-residency demo |
| `ipc` | Siemens Edge IPC or industrial PC | WFC/SPIDR near-OT workflow execution |
| `local_server` | Local workstation or plant server | Initial PoC, offline eval, dashboard evidence |
| `cloud_proxy` | HTTPS API World proxy to Wearedge backend | Xcelerator API World publication and subscription |

Environment values:

```powershell
$env:WEAREDGE_DEPLOYMENT_MODE="jetson"
$env:WEAREDGE_EDGE_NODE_ID="jetson-demo-01"
```

## Enterprise Group Narrative

Use this wording in pitch materials:

```text
Wearedge 的优势不是“会回答问题”，而是把工业智能体运行时放进产线边缘节点，让 AI 决策贴近设备、贴近数据、贴近工人，再由工易魔方把它编排成安全可审批的工业工作流。
```

## Evidence Boundary

- Current Workflow Canvas decision metrics are offline/simulated until live WFC/Xcelerator logs are captured.
- Current edge runtime evidence comes from repository PoC records, Jetson runbooks, M400 contract docs, and local smoke tests.
- Production OT writes require site authorization, WFC/SPIDR workflow controls, and human approval.
