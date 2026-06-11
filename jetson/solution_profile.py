from __future__ import annotations

from dataclasses import dataclass


SOLUTION_PROFILE_VERSION = "wearedge-industrial-agent-solution.v1"


@dataclass(frozen=True)
class RuntimeProfileInput:
    model: str
    model_variant: str
    llama_base_url: str
    deployment_mode: str
    edge_node_id: str


def build_solution_profile(runtime: RuntimeProfileInput) -> dict[str, object]:
    deployment_mode = runtime.deployment_mode.strip().lower() or "local_server"
    if deployment_mode not in {"jetson", "ipc", "local_server", "cloud_proxy"}:
        deployment_mode = "local_server"

    return {
        "ok": True,
        "api_version": SOLUTION_PROFILE_VERSION,
        "solution_name": "Wearedge Industrial AI Agent",
        "industrial_problem": {
            "name": "cross-domain abnormal-event decision for flexible multi-SKU production lines",
            "plain_language": (
                "When equipment, quality, energy, and changeover signals conflict, line teams need a fast, "
                "evidence-backed decision that can enter a safe Workflow Canvas approval loop."
            ),
            "target_scene": (
                "Automotive components, electronics assembly, packaging, food, or pharma lines with frequent "
                "SKU changes, quality containment pressure, maintenance risk, and energy optimization goals."
            ),
            "pain_points": [
                "MES, QMS, EMS, CMMS, device signals, and operator evidence are split across systems.",
                "Root-cause and action priority depend on senior operator experience and manual coordination.",
                "Cloud-only AI chatbots do not fit low-latency, data-residency, or OT safety requirements.",
                "High-risk actions such as stop, release, parameter change, or load shift require approval.",
            ],
        },
        "edge_runtime": {
            "node_id": runtime.edge_node_id,
            "deployment_mode": deployment_mode,
            "supported_deployment_modes": ["jetson", "ipc", "local_server", "cloud_proxy"],
            "data_residency": "Production images, local KB, evidence, and audit logs can remain on the edge node.",
        },
        "model_runtime": {
            "primary_model": runtime.model,
            "model_variant": runtime.model_variant,
            "runtime": "llama.cpp llama-server with OpenAI-compatible /v1/chat/completions",
            "base_url": runtime.llama_base_url,
            "default_poc_model": "Gemma 4 E2B multimodal GGUF plus mmproj vision projector",
            "model_role": [
                "interpret first-person images or operator prompts",
                "summarize industrial evidence into structured fields",
                "generate explainable recommendations for humans and downstream systems",
            ],
            "not_allowed_to_do": [
                "direct PLC or robot control",
                "final product release or scrap disposition",
                "unapproved production stop, restart, recipe change, or energy load shift",
            ],
        },
        "agent_system": {
            "runtime_style": "bounded industrial multi-agent workflow",
            "agents": [
                {
                    "id": "maintenance",
                    "role": "predictive maintenance, threshold evidence, root-cause candidates, work-order recommendation",
                    "owner": "maintenance_engineer",
                },
                {
                    "id": "quality",
                    "role": "defect containment, inspection expansion, quality-plan and QMS event recommendation",
                    "owner": "quality_engineer",
                },
                {
                    "id": "energy",
                    "role": "load forecast, idle or peak signal review, bounded energy optimization recommendation",
                    "owner": "energy_manager",
                },
                {
                    "id": "flexible_production",
                    "role": "SKU changeover, released checklist, line clearance, first-piece verification",
                    "owner": "line_lead",
                },
                {
                    "id": "workflow_canvas",
                    "role": "resource binding, Python Function Block call, data-table writeback, dashboard, approval gate",
                    "owner": "workflow_owner",
                },
            ],
        },
        "decision_mechanism": {
            "type": "deterministic KPI and rule guarded decision engine",
            "code_entry": "jetson.competition.build_competition_decision",
            "model_dependency": "not required for /v1/workflow-canvas/decision",
            "key_metrics_matrix": {
                "maintenance": ["f1_pct", "warning_lead_time_hours", "root_cause_top3_pct", "vibration_rms_mm_s"],
                "quality": ["defect_rate_pct", "detection_confidence_pct", "relative_improvement_pct"],
                "energy": ["forecast_accuracy_pct", "saving_pct", "idle_kw"],
                "flexible_production": ["schedule_efficiency_gain_pct", "component_reuse_pct", "target_sku"],
                "workflow_canvas": ["existing_component_use_pct", "new_component_reuse_potential_pct"],
            },
            "selection_logic": [
                "normalize requested agent directions",
                "score each direction against competition and plant-readiness targets",
                "assign status, priority, evidence, recommendation, workflow blocks, and required confirmations",
                "choose the primary direction by priority first, then score",
                "merge required confirmations into HumanApprovalGate inputs",
            ],
            "safety_boundary": (
                "The model explains evidence; deterministic guards and Workflow Canvas HumanApprovalGate "
                "decide action boundaries."
            ),
        },
        "platform_integration": {
            "xcelerator": {
                "openapi_spec": "openapi/wearedge-xcelerator-apiworld.openapi.json",
                "profile_endpoint": "/v1/industrial-agent/solution-profile",
                "decision_endpoint": "/v1/workflow-canvas/decision",
            },
            "gongyi_mofang": {
                "resource_block": "Wearedge Agent Service",
                "resource_parameters": [
                    "agentHost",
                    "agentPort",
                    "apiKeyRef",
                    "deploymentMode",
                    "plantId",
                    "lineId",
                ],
                "python_function_block": "CallWearedgeDecisionApi",
                "data_table": "wearedgeDecision",
                "human_gate": "HumanApprovalGate",
            },
        },
        "validation_evidence": {
            "offline_dataset": "evals/competition_offline_dataset.jsonl",
            "offline_evaluator": "scripts/run_competition_eval.py",
            "offline_report": "docs/competition-offline-eval-report.md",
            "wfc_smoke": "scripts/smoke_workflow_canvas_decision.py",
            "live_evidence_verifier": "scripts/verify_live_evidence.py",
        },
        "competition_delivery": {
            "technical_solution": "docs/submission/technical-solution.md",
            "business_plan": "docs/submission/business-plan.md",
            "registration_fields": "docs/submission/registration-fields.md",
            "demo_script": "docs/submission/demo-script.md",
            "evidence_index": "docs/submission/poc-evidence-index.md",
        },
    }
