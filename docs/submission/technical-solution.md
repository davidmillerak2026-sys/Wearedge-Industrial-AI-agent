# Technical Solution Draft

更新日期：2026-06-04

## Architecture

Wearedge uses a bounded industrial-agent runtime:

```text
WFC/MES/QMS/EMS/CMMS context
  -> Wearedge Agent Service
  -> deterministic competition evaluator
  -> collaborative decision
  -> Workflow Canvas blocks
  -> data table + Dashboard + HumanApprovalGate
```

## Core Runtime

- FastAPI gateway: `/v1/infer`, `/v1/workflow-canvas/decision`, `/healthz`.
- Agent routing: maintenance, quality, energy, flexible production, work instruction, changeover, hazard.
- Output contracts: structured fields for each mode.
- Deterministic guards: context guard, IQC guard, released-source guard, maintenance threshold evaluator, energy confirmation guard.
- Evidence storage: local sample KB, quality plan, released checklist, JSONL audit.

## Workflow Canvas Integration

工易魔方通过 `Wearedge Agent Service` 资源块绑定 API 地址，再由 `CallWearedgeDecisionApi` Python Function Block POST JSON 到 `/v1/workflow-canvas/decision`。输出写入全局数据表和 Dashboard，高风险动作进入 `HumanApprovalGate`。

## Offline Validation

`scripts/run_competition_eval.py` reads `evals/competition_offline_dataset.jsonl` and produces `docs/competition-offline-eval-report.md`. The report is an offline/simulated validation artifact and must be replaced or supplemented by WFC/Xcelerator PoC logs during later rounds.

## Edge Deployment

Current runtime supports local Python/FastAPI deployment and migrated Jetson deployment documents. For competition PoC, run local API first; then bind WFC Python Function Block to the API host and port.

## Safety And Compliance

The system does not let model text directly write OT controls. All high-risk outcomes carry required confirmations and residual risk. Final production control must remain inside approved WFC/SPIDR/PLC workflows with human approval where required.
