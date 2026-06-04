# Wearedge Industrial AI Agent

Competition engineering workspace for the 11th "Maker China" Industrial Agent track, focused on the Siemens Xcelerator / Workflow Canvas scenario.

This repository now carries the WearEdge Pro AI agent runtime needed for code validation and competition optimization.

## Direction

Wearedge is positioned as a multi-agent industrial decision and execution system for flexible, reconfigurable production lines. The target demo path is:

1. Detect an equipment, quality, or production-change event.
2. Gather evidence from MES, device signals, quality data, energy data, and maintenance history.
3. Run bounded agent diagnosis and collaborative decision-making.
4. Return an explainable recommendation with confidence, root cause, and residual risk.
5. Execute or simulate the approved action through Workflow Canvas.
6. Write results back to dashboards, logs, and work orders.

## Runtime

The migrated runtime comes from WearEdge Pro and includes:

- `jetson/`: FastAPI gateway and industrial agent runtime. It provides `/healthz`, `/v1/infer`, `/v1/workflow-canvas/decision`, audit queries, agent routing, output-contract validation, maintenance sessions, IQC guards, energy-management guards, released-source guards, action cards, and integration events.
- `industrial-rag-agent/`: local-first industrial RAG package for SOP, maintenance logs, quality documents, and workflow answers.
- `tests/`: runtime contract, agent loop, maintenance KB, IQC, released source, audit, and API tests.
- `scripts/`: setup, service launch, smoke tests, model download/build helpers, and POC validation.
- `deploy/`: systemd service templates for the gateway and local llama runtime.
- `data/`: small sample maintenance KB, IQC quality plan, and released-source examples.
- `docs/`: competition analysis plus migrated architecture, evidence, deployment, benchmark, and POC notes.

Raw competition attachments and extracted text are kept locally in `source_materials/` and `extracted_texts/`; they are intentionally ignored by Git.

## Quick Start

```powershell
python -m pip install --upgrade pip
python -m pip install pytest httpx
python -m pip install -r jetson/requirements.txt
python -m pip install -e industrial-rag-agent
python -m pytest tests industrial-rag-agent/tests
```

Run the API locally after configuring `.env` from `.env.example`:

```powershell
python -m uvicorn jetson.app:app --host 127.0.0.1 --port 8081
```

Workflow Canvas / Gongyi Mofang can call the competition decision endpoint with JSON from a Python Function Block:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8081/v1/workflow-canvas/decision `
  -ContentType application/json `
  -Body '{"stage":"final","selected_directions":["maintenance","quality","energy","flexible_production","workflow_canvas"],"context":{"maintenance":{"f1_pct":88,"warning_lead_time_hours":30,"root_cause_top3_pct":92},"quality":{"relative_improvement_pct":6},"energy":{"forecast_accuracy_pct":96,"saving_pct":12},"production":{"schedule_efficiency_gain_pct":22},"workflow_canvas":{"existing_component_use_pct":72}}}'
```

## Competition Targets

- Initial round: single-agent core capability plus technical plan and prototype code, or an executable Workflow Canvas workflow.
- Final round: at least three agent directions combined into one solution.
- Runtime target: response latency <= 500 ms for interactive decisions.
- Decision target: decision accuracy >= 90%.
- Maintenance target: F1 Score > 85%, warning lead time > 24 hours, root-cause Top 3 hit rate > 90%.
- Energy target: forecast accuracy >= 95% and verified saving estimate >= 10%.
- Quality target: detection or yield relative improvement >= 5%.
- Flexible production target: schedule optimization efficiency gain >= 20%.

## Notes

Models, generated runtime artifacts, deployment tarballs, local RAG indexes, and media outputs are ignored by Git. Keep reusable evidence in Markdown/JSON under `docs/`; keep large or local-only artifacts outside the repository history.
