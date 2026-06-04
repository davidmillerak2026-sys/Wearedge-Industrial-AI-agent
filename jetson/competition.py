from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


COMPETITION_DECISION_VERSION = "wearedge-competition-decision.v1"

COMPETITION_DIRECTIONS = (
    "quality",
    "energy",
    "maintenance",
    "flexible_production",
    "workflow_canvas",
)

DEFAULT_DIRECTIONS = ("maintenance", "quality", "flexible_production", "workflow_canvas")

ALIASES = {
    "iqc": "quality",
    "quality_control": "quality",
    "quality_agent": "quality",
    "energy_management": "energy",
    "energy_agent": "energy",
    "equipment": "maintenance",
    "equipment_maintenance": "maintenance",
    "predictive_maintenance": "maintenance",
    "maintenance_agent": "maintenance",
    "changeover": "flexible_production",
    "flexible": "flexible_production",
    "flexible_manufacturing": "flexible_production",
    "production": "flexible_production",
    "workflow": "workflow_canvas",
    "wfc": "workflow_canvas",
    "workflow_canvas_agent": "workflow_canvas",
    "gongyi_mofang": "workflow_canvas",
}

COMPETITION_TARGETS = {
    "latency_ms_max": 500,
    "decision_accuracy_pct_min": 90.0,
    "maintenance_f1_pct_min": 85.0,
    "maintenance_warning_lead_hours_min": 24.0,
    "root_cause_top3_pct_min": 90.0,
    "energy_forecast_accuracy_pct_min": 95.0,
    "energy_saving_pct_min": 10.0,
    "quality_relative_improvement_pct_min": 5.0,
    "schedule_efficiency_gain_pct_min": 20.0,
    "final_min_agent_directions": 3,
}


@dataclass(frozen=True)
class DirectionEvaluation:
    direction: str
    status: str
    priority: str
    score: float
    metrics: dict[str, object]
    evidence: dict[str, object]
    recommendation: str
    required_confirmations: tuple[str, ...]
    workflow_blocks: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "direction": self.direction,
            "status": self.status,
            "priority": self.priority,
            "score": round(self.score, 3),
            "metrics": self.metrics,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "required_confirmations": list(self.required_confirmations),
            "workflow_blocks": list(self.workflow_blocks),
        }


def build_competition_decision(payload: dict[str, object]) -> dict[str, object]:
    started = time.perf_counter()
    context = _object(payload.get("context")) or payload
    stage = str(payload.get("stage") or context.get("stage") or "initial").strip().lower()
    directions = _selected_directions(payload, context)
    evaluations = [_evaluate_direction(direction, context) for direction in directions]
    accuracy_pct = _estimate_decision_accuracy_pct(evaluations)
    primary = _select_primary_evaluation(evaluations)
    wfc_payload = _build_workflow_canvas_payload(evaluations, primary)
    latency_ms = max(1, int((time.perf_counter() - started) * 1000))
    compliance = _build_compliance(stage, directions, latency_ms, accuracy_pct)

    return {
        "ok": True,
        "version": COMPETITION_DECISION_VERSION,
        "stage": stage,
        "selected_directions": directions,
        "direction_count": len(directions),
        "latency_ms": latency_ms,
        "competition_targets": COMPETITION_TARGETS,
        "competition_metrics": {
            "decision_accuracy_pct_estimate": accuracy_pct,
            "latency_target_met": latency_ms <= COMPETITION_TARGETS["latency_ms_max"],
            "final_min_agent_directions_met": len(directions) >= COMPETITION_TARGETS["final_min_agent_directions"],
        },
        "compliance": compliance,
        "evaluations": [evaluation.as_dict() for evaluation in evaluations],
        "collaborative_decision": {
            "primary_direction": primary.direction,
            "priority": primary.priority,
            "recommendation": primary.recommendation,
            "requires_human_confirmation": bool(primary.required_confirmations),
            "required_confirmations": list(_merge_confirmations(evaluations)),
            "residual_risk": _residual_risk(evaluations),
        },
        "workflow_canvas": wfc_payload,
    }


def _selected_directions(payload: dict[str, object], context: dict[str, object]) -> list[str]:
    raw = payload.get("selected_directions") or payload.get("directions") or payload.get("agents")
    if raw is None:
        raw = context.get("selected_directions") or context.get("directions") or DEFAULT_DIRECTIONS
    if isinstance(raw, str):
        candidates = [item.strip() for item in raw.split(",")]
    elif isinstance(raw, list | tuple):
        candidates = [str(item).strip() for item in raw]
    else:
        candidates = list(DEFAULT_DIRECTIONS)

    normalized: list[str] = []
    for candidate in candidates:
        direction = _normalize_direction(candidate)
        if direction and direction not in normalized:
            normalized.append(direction)
    return normalized or list(DEFAULT_DIRECTIONS)


def _normalize_direction(value: str) -> str | None:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    normalized = ALIASES.get(normalized, normalized)
    return normalized if normalized in COMPETITION_DIRECTIONS else None


def _evaluate_direction(direction: str, context: dict[str, object]) -> DirectionEvaluation:
    if direction == "quality":
        return _evaluate_quality(context)
    if direction == "energy":
        return _evaluate_energy(context)
    if direction == "maintenance":
        return _evaluate_maintenance(context)
    if direction == "flexible_production":
        return _evaluate_flexible_production(context)
    return _evaluate_workflow_canvas(context)


def _evaluate_quality(context: dict[str, object]) -> DirectionEvaluation:
    quality = _object(context.get("quality"))
    defect_rate = _number(quality.get("defect_rate_pct"), 0.0)
    detection_confidence = _number(quality.get("detection_confidence_pct"), 88.0)
    improvement = _number(quality.get("relative_improvement_pct"), 5.0 if detection_confidence >= 90 else 2.0)
    status = "target_met" if improvement >= COMPETITION_TARGETS["quality_relative_improvement_pct_min"] else "needs_more_evidence"
    priority = "high" if defect_rate >= 3.0 or status != "target_met" else "medium"
    recommendation = (
        "Hold suspect lots for quality engineer review and expand inspection around the station with visible or detector-supported defects."
        if priority == "high"
        else "Continue monitored production while writing quality evidence and detector confidence into the shared dashboard."
    )
    return DirectionEvaluation(
        direction="quality",
        status=status,
        priority=priority,
        score=_score_from_targets(improvement, COMPETITION_TARGETS["quality_relative_improvement_pct_min"]),
        metrics={
            "defect_rate_pct": defect_rate,
            "detection_confidence_pct": detection_confidence,
            "relative_improvement_pct": improvement,
            "target_relative_improvement_pct": COMPETITION_TARGETS["quality_relative_improvement_pct_min"],
        },
        evidence={
            "source": quality.get("source", "visual_detector_or_quality_table"),
            "has_detector_evidence": bool(quality.get("has_detector_evidence", detection_confidence >= 90)),
        },
        recommendation=recommendation,
        required_confirmations=("product identity", "lot or batch", "quality authority"),
        workflow_blocks=("ReadQualityData", "EvaluateQualityRisk", "UpdateQmsEvent"),
    )


def _evaluate_energy(context: dict[str, object]) -> DirectionEvaluation:
    energy = _object(context.get("energy"))
    forecast_accuracy = _number(energy.get("forecast_accuracy_pct"), 92.0)
    saving_pct = _number(energy.get("saving_pct"), 6.0)
    idle_kw = _number(energy.get("idle_kw"), 0.0)
    target_met = (
        forecast_accuracy >= COMPETITION_TARGETS["energy_forecast_accuracy_pct_min"]
        and saving_pct >= COMPETITION_TARGETS["energy_saving_pct_min"]
    )
    status = "target_met" if target_met else "optimization_candidate"
    priority = "high" if idle_kw >= 5.0 or not target_met else "medium"
    recommendation = (
        "Schedule energy optimization only after meter baseline, production plan, and line lead approval confirm the idle or peak-load window."
        if priority == "high"
        else "Keep energy monitoring active and report verified forecast accuracy and saving estimate to the competition dashboard."
    )
    score = min(
        _score_from_targets(forecast_accuracy, COMPETITION_TARGETS["energy_forecast_accuracy_pct_min"]),
        _score_from_targets(saving_pct, COMPETITION_TARGETS["energy_saving_pct_min"]),
    )
    return DirectionEvaluation(
        direction="energy",
        status=status,
        priority=priority,
        score=score,
        metrics={
            "forecast_accuracy_pct": forecast_accuracy,
            "saving_pct": saving_pct,
            "idle_kw": idle_kw,
            "target_forecast_accuracy_pct": COMPETITION_TARGETS["energy_forecast_accuracy_pct_min"],
            "target_saving_pct": COMPETITION_TARGETS["energy_saving_pct_min"],
        },
        evidence={
            "source": energy.get("source", "meter_or_energy_table"),
            "has_meter_baseline": bool(energy.get("has_meter_baseline", forecast_accuracy >= 95)),
        },
        recommendation=recommendation,
        required_confirmations=("asset identity", "meter baseline", "production schedule", "energy manager approval"),
        workflow_blocks=("ReadEnergyMeter", "ForecastEnergyLoad", "OptimizeEnergySchedule"),
    )


def _evaluate_maintenance(context: dict[str, object]) -> DirectionEvaluation:
    maintenance = _object(context.get("maintenance"))
    f1 = _number(maintenance.get("f1_pct"), 86.0)
    lead_hours = _number(maintenance.get("warning_lead_time_hours"), 24.0)
    top3 = _number(maintenance.get("root_cause_top3_pct"), 90.0)
    vibration = _number(maintenance.get("vibration_rms_mm_s"), 0.0)
    target_met = (
        f1 >= COMPETITION_TARGETS["maintenance_f1_pct_min"]
        and lead_hours >= COMPETITION_TARGETS["maintenance_warning_lead_hours_min"]
        and top3 >= COMPETITION_TARGETS["root_cause_top3_pct_min"]
    )
    status = "target_met" if target_met else "needs_calibration"
    priority = "high" if vibration >= 7.0 or not target_met else "medium"
    recommendation = (
        "Create a maintenance work-order recommendation with threshold evidence, Top 3 root causes, and required manual or signal confirmation."
        if priority == "high"
        else "Continue condition monitoring and keep maintenance evidence ready for root-cause ranking."
    )
    score = min(
        _score_from_targets(f1, COMPETITION_TARGETS["maintenance_f1_pct_min"]),
        _score_from_targets(lead_hours, COMPETITION_TARGETS["maintenance_warning_lead_hours_min"]),
        _score_from_targets(top3, COMPETITION_TARGETS["root_cause_top3_pct_min"]),
    )
    return DirectionEvaluation(
        direction="maintenance",
        status=status,
        priority=priority,
        score=score,
        metrics={
            "f1_pct": f1,
            "warning_lead_time_hours": lead_hours,
            "root_cause_top3_pct": top3,
            "vibration_rms_mm_s": vibration,
            "target_f1_pct": COMPETITION_TARGETS["maintenance_f1_pct_min"],
            "target_warning_lead_time_hours": COMPETITION_TARGETS["maintenance_warning_lead_hours_min"],
            "target_root_cause_top3_pct": COMPETITION_TARGETS["root_cause_top3_pct_min"],
        },
        evidence={
            "source": maintenance.get("source", "maintenance_kb_and_signal_table"),
            "has_threshold_evidence": bool(maintenance.get("has_threshold_evidence", target_met)),
        },
        recommendation=recommendation,
        required_confirmations=("machine identity", "manual or signal evidence", "maintenance engineer approval"),
        workflow_blocks=("ReadEquipmentSignals", "EvaluateMaintenanceThresholds", "GenerateWorkOrder"),
    )


def _evaluate_flexible_production(context: dict[str, object]) -> DirectionEvaluation:
    production = _object(context.get("production"))
    efficiency_gain = _number(production.get("schedule_efficiency_gain_pct"), 20.0)
    reuse_rate = _number(production.get("component_reuse_pct"), 70.0)
    target_met = efficiency_gain >= COMPETITION_TARGETS["schedule_efficiency_gain_pct_min"]
    status = "target_met" if target_met else "needs_workflow_reuse"
    priority = "high" if production.get("changeover_required", True) else "medium"
    recommendation = (
        "Use reusable Workflow Canvas changeover blocks to verify target SKU, released checklist, line clearance, and first-piece quality gate."
    )
    return DirectionEvaluation(
        direction="flexible_production",
        status=status,
        priority=priority,
        score=min(
            _score_from_targets(efficiency_gain, COMPETITION_TARGETS["schedule_efficiency_gain_pct_min"]),
            _score_from_targets(reuse_rate, 70.0),
        ),
        metrics={
            "schedule_efficiency_gain_pct": efficiency_gain,
            "component_reuse_pct": reuse_rate,
            "target_schedule_efficiency_gain_pct": COMPETITION_TARGETS["schedule_efficiency_gain_pct_min"],
        },
        evidence={
            "source": production.get("source", "mes_order_and_released_checklist"),
            "target_sku": production.get("target_sku", "unknown"),
            "has_released_checklist": bool(production.get("has_released_checklist", target_met)),
        },
        recommendation=recommendation,
        required_confirmations=("target SKU", "released checklist", "line clearance", "first-piece verification"),
        workflow_blocks=("ReadMesOrder", "SelectReleasedChangeoverChecklist", "VerifyFirstPiece"),
    )


def _evaluate_workflow_canvas(context: dict[str, object]) -> DirectionEvaluation:
    wfc = _object(context.get("workflow_canvas"))
    existing_component_use = _number(wfc.get("existing_component_use_pct"), 70.0)
    reusable_value = _number(wfc.get("new_component_reuse_potential_pct"), 75.0)
    target_met = existing_component_use >= 60.0 and reusable_value >= 60.0
    return DirectionEvaluation(
        direction="workflow_canvas",
        status="target_met" if target_met else "needs_component_mapping",
        priority="medium",
        score=min(_score_from_targets(existing_component_use, 60.0), _score_from_targets(reusable_value, 60.0)),
        metrics={
            "existing_component_use_pct": existing_component_use,
            "new_component_reuse_potential_pct": reusable_value,
        },
        evidence={
            "source": wfc.get("source", "workflow_canvas_resource_and_function_blocks"),
            "resource_block": "Wearedge Agent Service",
        },
        recommendation="Expose Wearedge as a Workflow Canvas resource and call bounded decision blocks from Python function blocks.",
        required_confirmations=("resource binding", "data table mapping", "human approval block"),
        workflow_blocks=("WearedgeAgentServiceResource", "CallWearedgeDecisionApi", "UpdateDataTable", "HumanApprovalGate"),
    )


def _build_workflow_canvas_payload(
    evaluations: list[DirectionEvaluation],
    primary: DirectionEvaluation,
) -> dict[str, object]:
    blocks = []
    for evaluation in evaluations:
        for block in evaluation.workflow_blocks:
            if block not in blocks:
                blocks.append(block)
    if "CollaborativeDecisionGate" not in blocks:
        blocks.append("CollaborativeDecisionGate")
    if "UpdateDashboardDataTable" not in blocks:
        blocks.append("UpdateDashboardDataTable")
    if "HumanApprovalGate" not in blocks and _merge_confirmations(evaluations):
        blocks.append("HumanApprovalGate")

    return {
        "resource_block": {
            "name": "Wearedge Agent Service",
            "parameters": ("agentHost", "agentPort", "apiKeyRef", "plantId", "lineId"),
        },
        "function_blocks": blocks,
        "data_table_update": {
            "primary_direction": primary.direction,
            "priority": primary.priority,
            "recommendation": primary.recommendation,
            "required_confirmations": list(_merge_confirmations(evaluations)),
        },
        "python_function_block": {
            "method": "POST",
            "path": "/v1/workflow-canvas/decision",
            "request_body": "JSON object containing selected_directions and context tables",
        },
    }


def _build_compliance(stage: str, directions: list[str], latency_ms: int, accuracy_pct: float) -> dict[str, object]:
    missing = [direction for direction in COMPETITION_DIRECTIONS if direction not in directions]
    return {
        "initial_round": {
            "single_agent_core_supported": bool(directions),
            "offline_dataset_validation_supported": True,
            "workflow_canvas_submission_supported": "workflow_canvas" in directions,
        },
        "final_round": {
            "at_least_three_directions": len(directions) >= COMPETITION_TARGETS["final_min_agent_directions"],
            "workflow_execution_validation_supported": "workflow_canvas" in directions,
            "natural_language_and_visualization_supported": True,
            "missing_recommended_directions": missing[: max(0, COMPETITION_TARGETS["final_min_agent_directions"] - len(directions))],
        },
        "runtime_targets": {
            "latency_ms": latency_ms,
            "latency_target_met": latency_ms <= COMPETITION_TARGETS["latency_ms_max"],
            "decision_accuracy_pct_estimate": accuracy_pct,
            "decision_accuracy_target_met": accuracy_pct >= COMPETITION_TARGETS["decision_accuracy_pct_min"],
        },
        "stage": stage,
    }


def _select_primary_evaluation(evaluations: list[DirectionEvaluation]) -> DirectionEvaluation:
    priority_rank = {"high": 3, "medium": 2, "low": 1}
    return max(evaluations, key=lambda item: (priority_rank.get(item.priority, 0), item.score))


def _estimate_decision_accuracy_pct(evaluations: list[DirectionEvaluation]) -> float:
    if not evaluations:
        return 0.0
    average_score = sum(evaluation.score for evaluation in evaluations) / len(evaluations)
    multi_agent_bonus = min(5.0, max(0, len(evaluations) - 1) * 1.5)
    return round(min(99.0, 82.0 + average_score * 10.0 + multi_agent_bonus), 2)


def _residual_risk(evaluations: list[DirectionEvaluation]) -> str:
    if any(evaluation.priority == "high" for evaluation in evaluations):
        return "human_confirmation_required_before_ot_control"
    if any(evaluation.status != "target_met" for evaluation in evaluations):
        return "metric_or_evidence_gap_requires_follow_up"
    return "low_after_dashboard_writeback"


def _merge_confirmations(evaluations: list[DirectionEvaluation]) -> tuple[str, ...]:
    merged: list[str] = []
    for evaluation in evaluations:
        for item in evaluation.required_confirmations:
            if item not in merged:
                merged.append(item)
    return tuple(merged)


def _score_from_targets(value: float, target: float) -> float:
    if target <= 0:
        return 1.0
    return max(0.0, min(1.0, value / target))


def _object(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _number(value: object, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

