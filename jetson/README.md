# Jetson Runtime

This package contains the WearEdge Pro edge gateway that runs on Jetson.

## Responsibilities

| File | Purpose |
| --- | --- |
| [`app.py`](app.py) | FastAPI gateway, `/healthz`, `/v1/infer`, `/v1/workflow-canvas/decision`, `/v1/edge/runtime-profile`, audit query, and agent run endpoints. |
| [`competition.py`](competition.py) | Deterministic competition-target evaluator and Workflow Canvas decision payload builder. |
| [`llama_client.py`](llama_client.py) | Local llama.cpp chat and multimodal payload adapter. |
| [`config.py`](config.py) | Environment-driven runtime configuration. |
| [`output_contract.py`](output_contract.py) | Contract parsing, validation, and repair for stable machine-readable results. |
| [`agently_orchestrator.py`](agently_orchestrator.py) | Agent-style workflow orchestration, runtime stream, and action card generation. |
| [`agent_loop.py`](agent_loop.py) | Route selection, action decisions, and integration event shaping. |
| [`audit_log.py`](audit_log.py) | JSONL audit append/read helpers. |
| [`maintenance_session.py`](maintenance_session.py) | Multi-evidence maintenance session state. |
| [`maintenance_kb.py`](maintenance_kb.py) | Local maintenance knowledge retrieval. |
| [`iqc_quality_plan.py`](iqc_quality_plan.py) | Product-specific IQC plan lookup. |
| [`iqc_quality_eval.py`](iqc_quality_eval.py) | Deterministic IQC disposition guard. |
| [`released_source.py`](released_source.py) | Released work-instruction and changeover source guard. |

## Runtime Boundary

The model explains visual and contextual evidence. Deterministic guards decide whether an action can become an operator-facing action card, quality event, energy-management event, maintenance observation, or released-source recommendation.

## Workflow Canvas Entry

Use `POST /v1/workflow-canvas/decision` for Gongyi Mofang Python Function Blocks. It accepts JSON with `selected_directions` and `context` tables, then returns competition metrics, collaborative decision state, required confirmations, and reusable Workflow Canvas block names. `POST /v1/competition/decision` is the same local validation surface.

Use `GET /v1/edge/runtime-profile` for enterprise-group evidence that the Wearedge agent runtime can run on Jetson, IPC, local industrial PCs, or cloud proxy while remaining Workflow Canvas ready.

## Local Verification

```bash
cd ~/WearEdge-Pro
source .env
scripts/smoke_test.sh
```

See [`../docs/e2b-deployment-runbook.md`](../docs/e2b-deployment-runbook.md) for Jetson deployment details.
