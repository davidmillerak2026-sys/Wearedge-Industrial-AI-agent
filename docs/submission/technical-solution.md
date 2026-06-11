# Technical Solution Draft

更新日期：2026-06-09

## Architecture

Wearedge uses a bounded industrial-agent runtime that can run on edge compute:

```text
M400 / Camera / OPC UA / MES / QMS / EMS / CMMS context
  -> Wearedge Edge Agent Runtime on Jetson / IPC / local server
  -> Gongyi Mofang / Xcelerator orchestration
  -> deterministic competition evaluator
  -> collaborative decision
  -> Workflow Canvas blocks
  -> data table + Dashboard + HumanApprovalGate
```

## Core Runtime

- FastAPI gateway: `/v1/infer`, `/v1/workflow-canvas/decision`, `/v1/edge/runtime-profile`, `/healthz`.
- Solution profile: `/v1/industrial-agent/solution-profile` explains the target industrial problem, model runtime, agent split, KPI decision matrix, platform integration, and validation evidence.
- Agent routing: maintenance, quality, energy, flexible production, work instruction, changeover, hazard.
- Output contracts: structured fields for each mode.
- Deterministic guards: context guard, IQC guard, released-source guard, maintenance threshold evaluator, energy confirmation guard.
- Evidence storage: local sample KB, quality plan, released checklist, JSONL audit.

## Model And Decision Mechanism

The edge inference PoC uses Gemma 4 E2B through `llama.cpp` / `llama-server`, exposed to the gateway as an OpenAI-compatible `/v1/chat/completions` service. The model is used for image/prompt interpretation, evidence explanation, and structured recommendations.

The Workflow Canvas decision endpoint does not require the model to make the final production decision. `/v1/workflow-canvas/decision` uses `jetson.competition.build_competition_decision()` to score maintenance, quality, energy, flexible production, and Workflow Canvas directions against deterministic KPIs, then selects the primary direction by priority and score. High-risk outcomes are passed to `HumanApprovalGate`.

## Workflow Canvas Integration

工易魔方通过 `Wearedge Agent Service` 资源块绑定端侧 API 地址，再由 `CallWearedgeDecisionApi` Python Function Block POST JSON 到 `/v1/workflow-canvas/decision`。输出写入全局数据表和 Dashboard，高风险动作进入 `HumanApprovalGate`。当前资源块原型位于 `wfc-blocks/wearedge-agent-service/`。

## Edge Agent Runtime

`GET /v1/edge/runtime-profile` exposes deployment mode, local inference readiness, Workflow Canvas readiness, industrial connectors, and safety boundaries. It is intended for Xcelerator / Gongyi Mofang screenshots and proves that Wearedge can run on Jetson, Siemens Edge IPC, local industrial PC, or plant edge server instead of remaining a cloud-only chatbot.

## Industrial Connector Path

The first PoC uses simulated MES, quality, energy, maintenance, and WFC context tables. The platform-ready path is OPC UA / MQTT / S7 or MES/QMS/EMS/CMMS integration through WFC resource blocks, then Wearedge receives normalized context JSON and returns bounded decisions. Direct OT writeback remains outside model authority.

## Offline Validation

`scripts/run_competition_eval.py` reads `evals/competition_offline_dataset.jsonl` and produces `docs/competition-offline-eval-report.md`. The report is an offline/simulated validation artifact and must be replaced or supplemented by WFC/Xcelerator PoC logs during later rounds.

## Edge Deployment

Current runtime supports local Python/FastAPI deployment and migrated Jetson deployment documents. For competition PoC, run local API first; then bind WFC Python Function Block to the API host and port. For enterprise-group differentiation, capture the edge profile and Jetson/M400 evidence before the final demo video.

## Safety And Compliance

The system does not let model text directly write OT controls. All high-risk outcomes carry required confirmations and residual risk. Final production control must remain inside approved WFC/SPIDR/PLC workflows with human approval where required.
