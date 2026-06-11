# Defense Q&A Playbook

Updated: 2026-06-11

Use this during rehearsal and final review. Answers are intentionally concise so they can be spoken in 30-60 seconds.

## Opening Answer

Wearedge solves the cross-domain coordination problem in flexible manufacturing lines: order changes, changeover, equipment health, quality risk, and energy windows are usually handled by separate systems and people. Wearedge puts an industrial agent runtime on edge compute such as Jetson, IPC, or a local industrial PC, then uses Siemens Xcelerator / Gongyi Mofang to orchestrate workflow, human approval, and data writeback. The result is a bounded, auditable, multi-agent decision workflow instead of a generic industrial chatbot.

## Likely Questions

### 1. What exact industrial problem does Wearedge solve?

It targets multi-SKU discrete manufacturing lines where maintenance, quality, energy, and production decisions affect each other but are handled in separate silos. A typical scenario is: urgent order change triggers changeover pressure, a gearbox or station signal becomes abnormal, quality defect risk rises, and energy windows need adjustment. Wearedge combines those contexts into one collaborative decision with priority, recommendation, evidence, residual risk, and required human confirmation.

Evidence: `docs/submission/business-plan.md`, `docs/workflow-canvas-api-schema.md`, `docs/submission/evidence/workflow-canvas-decision.json`.

### 2. Why is this innovative?

The innovation is not another chatbot interface. Wearedge runs the industrial agent runtime close to the production line on edge compute, keeps data and audit logs near the factory, and exposes a structured API that Gongyi Mofang can orchestrate as workflow blocks. It combines multi-agent reasoning, deterministic KPI guards, resource blocks, data-table writeback, Dashboard display, and HumanApprovalGate.

Evidence: `docs/edge-agent-runtime-for-xcelerator.md`, `wfc-blocks/wearedge-agent-service/`, `openapi/wearedge-xcelerator-apiworld.openapi.json`.

### 3. What model do you use?

The edge inference PoC is designed around Gemma 4 E2B through `llama.cpp` / `llama-server`, exposed as an OpenAI-compatible local endpoint. The model is used for evidence interpretation, natural-language explanation, and structured recommendations. The Workflow Canvas decision endpoint does not rely on the model to make final production actions; it uses deterministic KPI scoring and safety guards.

Evidence: `docs/submission/technical-solution.md`, `docs/submission/business-plan.md`, `docs/submission/evidence/solution-profile.json`.

### 4. What mechanism actually makes decisions?

The decision mechanism is a KPI matrix plus deterministic guards. Maintenance, quality, energy, flexible production, and Workflow Canvas directions are scored against measurable indicators such as maintenance F1, warning lead time, root-cause top-3, energy forecast accuracy, saving estimate, quality improvement, schedule efficiency, and latency. The final output selects a primary direction and routes high-risk actions to HumanApprovalGate.

Evidence: `scripts/run_competition_eval.py`, `docs/competition-offline-eval-report.md`, `jetson/competition.py`.

### 5. How does it connect to Gongyi Mofang?

Gongyi Mofang defines `Wearedge Agent Service` as a resource and uses the `CallWearedgeDecisionApi` Python Function Block to POST context JSON to `/v1/workflow-canvas/decision`. The response is written to global data tables, shown in Dashboard/ui-builder, and routed to human approval for high-risk actions.

Evidence: `docs/workflow-canvas-poc-runbook.md`, `wfc-blocks/wearedge-agent-service/`, `workflows/wfc_call_wearedge_decision_fb_main.py`.

### 6. What live platform evidence do you have?

We have Xcelerator draft application/API service evidence, OpenAPI import evidence, WFC project evidence, Python block evidence, data-table field evidence, WFC `fb_main.py` saved evidence, debug entry, and `Workflow is ready` log-manager evidence. Dashboard, final `ok=true` WFC run log, and HumanApprovalGate are currently fallback/mock/API-smoke assets and are explicitly marked as such until live WFC replacement is captured.

Evidence: `docs/submission/platform-live-evidence-status-20260609.md`, `docs/submission/live-platform-evidence-runbook.md`.

### 7. How do you avoid unsafe OT control?

The model never directly writes PLC, robot, stop-line, or quality-release actions. Wearedge emits recommendations, evidence, required confirmations, residual risk, and owner roles. Final production control must stay inside approved WFC/SPIDR/PLC workflows and, for high-risk actions, pass HumanApprovalGate.

Evidence: `docs/submission/technical-solution.md`, `docs/workflow-canvas-api-schema.md`, `docs/submission/judging-scorecard-evidence-map.md`.

### 8. What is the target customer?

The first target customers are multi-SKU discrete manufacturers, including automotive parts, electronics assembly, packaging, food/pharma packaging, and other lines where changeover, downtime, defect containment, and energy use must be coordinated. The best initial customers already use or plan to use Siemens Xcelerator, Gongyi Mofang, MES, QMS, EMS, or CMMS systems.

Evidence: `docs/submission/business-plan.md`, `docs/submission/registration-fields.md`.

### 9. What is the business model?

The model combines joint PoC services, Gongyi Mofang scenario template licensing, edge runtime deployment integration, and ongoing operations support for knowledge base updates, metrics review, rule maintenance, and model upgrades. This fits Siemens co-creation because the solution can become repeatable industry templates.

Evidence: `docs/submission/business-plan.md`, `docs/siemens-xcelerator-co-creation-onepager.md`.

### 10. What is already completed and what remains?

Completed repository-controlled assets include API endpoints, OpenAPI, WFC resource package, offline evaluator, generated submission evidence, demo video generator, final submission bundle builder, and human-action templates. Remaining final work is enterprise-owned: company/contact information, signed IP/no-dispute and no-adverse-record statements, final registration screenshots, and replacing fallback WFC `04/05/06` evidence with real live WFC closure when available.

Evidence: `docs/submission/submission-package-manifest.md`, `scripts/verify_submission_package.py`, `scripts/verify_live_evidence.py`.

## Hard Questions

### Are your metrics real production results?

No. Current metrics are offline/simulated engineering validation for first-round readiness. We label them honestly and use them to prove the evaluator, schema, and KPI logic work. Real customer production metrics will be collected in the joint PoC phase.

### Why should judges trust the PoC?

Because the evidence is reproducible: scripts, datasets, OpenAPI, WFC resource package, smoke tests, generated evidence, and submission bundle are in the repository. We separate live evidence from fallback/mock evidence and do not overclaim production deployment.

### What if Gongyi Mofang live execution fails during the demo?

We use a dual-path demo. Path A is the live platform route. Path B is local API smoke, generated Dashboard mock, recorded video, Xcelerator API draft, WFC project screenshots, and the repo-controlled submission bundle. The fallback is clearly labeled and does not claim live WFC success.

### Why Siemens?

Xcelerator and Gongyi Mofang provide the platform layer for API management, workflow orchestration, IT/OT integration, data tables, Dashboard, and approval. Wearedge provides the edge industrial agent runtime and bounded decision API. The split is clean and co-creation-friendly.

## Closing Answer

Wearedge's strongest point is the combination of edge deployment, platform orchestration, deterministic safety boundaries, and repeatable engineering evidence. It is not just a demo of AI answers; it is a path to a Siemens-compatible industrial agent product that can become reusable templates for flexible manufacturing lines.
