from __future__ import annotations

from dataclasses import dataclass

from .agent_profiles import normalize_agent_mode


EVIDENCE_PLAN_VERSION = "wear-edge-evidence-plan.v1"


@dataclass(frozen=True)
class EvidenceItem:
    name: str
    kind: str
    status: str
    purpose: str
    required_for: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "purpose": self.purpose,
            "required_for": list(self.required_for),
        }


@dataclass(frozen=True)
class EvidencePlan:
    version: str
    mode: str
    current_sources: tuple[EvidenceItem, ...]
    planned_tools: tuple[EvidenceItem, ...]
    missing_tools: tuple[str, ...]
    policy: str

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "mode": self.mode,
            "current_sources": [item.as_dict() for item in self.current_sources],
            "planned_tools": [item.as_dict() for item in self.planned_tools],
            "missing_tools": list(self.missing_tools),
            "policy": self.policy,
        }


def build_evidence_plan(
    *,
    mode: str,
    device: dict[str, object],
    image_bytes: int,
    needs_ocr: bool,
    high_detail: bool,
    available_tools: tuple[str, ...] = (),
) -> EvidencePlan:
    resolved = normalize_agent_mode(mode)
    current_sources = (
        EvidenceItem(
            name="m400_image",
            kind="edge_capture",
            status="available",
            purpose=f"M400 frame is present with {image_bytes} bytes for visible-context reasoning.",
        ),
        EvidenceItem(
            name="device_context",
            kind="edge_metadata",
            status="available" if device else "missing",
            purpose="Device id, timestamp, location hint, and capture mode are used for traceability.",
        ),
        EvidenceItem(
            name="ocr_attention",
            kind="runtime_hint",
            status="requested" if needs_ocr else "not_requested",
            purpose="Marks whether labels, HMI text, SKU, or small print need higher attention.",
        ),
        EvidenceItem(
            name="high_detail_visual",
            kind="runtime_hint",
            status="requested" if high_detail else "not_requested",
            purpose="Marks whether image detail should be preserved for small defects or machine cues.",
        ),
    )
    planned_tools = _planned_tools_for(resolved, available_tools=available_tools)
    missing_tools = tuple(item.name for item in planned_tools if item.status == "not_connected")
    return EvidencePlan(
        version=EVIDENCE_PLAN_VERSION,
        mode=resolved,
        current_sources=current_sources,
        planned_tools=planned_tools,
        missing_tools=missing_tools,
        policy=_policy_for(resolved),
    )


def build_evidence_prompt_context(plan: EvidencePlan) -> str:
    current = ", ".join(item.name for item in plan.current_sources if item.status in {"available", "requested"})
    missing = ", ".join(plan.missing_tools) if plan.missing_tools else "none"
    return (
        "Evidence context:\n"
        f"- current={current}.\n"
        f"- not_connected={missing}.\n"
        f"- policy={plan.policy}\n"
        "Do not claim unavailable external evidence."
    )


def _planned_tools_for(mode: str, *, available_tools: tuple[str, ...] = ()) -> tuple[EvidenceItem, ...]:
    tools = {
        "maintenance": (
            EvidenceItem(
                "asset_registry",
                "mcp_tool",
                "not_connected",
                "Match visible machine identity to asset id and station.",
                ("machine-specific recommendation",),
            ),
            EvidenceItem(
                "telemetry_history",
                "mcp_tool",
                "not_connected",
                "Fetch vibration, temperature, pressure, runtime, or alarm trend evidence.",
                ("predictive risk", "maintenance scheduling"),
            ),
            EvidenceItem(
                "manual_kb",
                "rag_tool",
                "available",
                "Retrieve released maintenance manual thresholds and inspection points.",
                ("evidence_needed", "work order draft"),
            ),
            EvidenceItem(
                "work_order_history",
                "cmms_tool",
                "not_connected",
                "Check recent failures, repairs, and open maintenance work.",
                ("maintenance escalation",),
            ),
        ),
        "iqc": (
            EvidenceItem(
                "visual_defect_detector",
                "vision_tool",
                "not_connected",
                "Produce defect boxes, class scores, and image evidence before VLM explanation.",
                ("quality risk", "pass decision"),
            ),
            EvidenceItem(
                "quality_plan",
                "rag_tool",
                "available",
                "Retrieve released sampling plan, defect catalog, limits, and disposition authority.",
                ("quality hold", "release review"),
            ),
            EvidenceItem(
                "lot_context",
                "mes_tool",
                "not_connected",
                "Resolve product, station, lot, shift, and adjacent-unit containment scope.",
                ("expand inspection",),
            ),
        ),
        "changeover": (
            EvidenceItem(
                "sku_recipe",
                "mes_tool",
                "not_connected",
                "Resolve target SKU, recipe, tooling, label, and change-part matrix.",
                ("changeover continuation", "restart verification"),
            ),
            EvidenceItem(
                "changeover_checklist",
                "rag_tool",
                "available",
                "Retrieve released line-clearance and conversion checklist steps.",
                ("operator guidance",),
            ),
            EvidenceItem(
                "first_piece_plan",
                "qms_tool",
                "not_connected",
                "Retrieve first-piece verification and approval requirements.",
                ("startup authorization",),
            ),
        ),
        "wi": (
            EvidenceItem(
                "wi_repository",
                "rag_tool",
                "available",
                "Retrieve released work instruction revision by machine and station.",
                ("guided operation",),
            ),
            EvidenceItem(
                "machine_identity",
                "mcp_tool",
                "not_connected",
                "Confirm machine, station, tooling, and allowed operating context.",
                ("operator guidance",),
            ),
        ),
        "hazard": (
            EvidenceItem(
                "ppe_detector",
                "vision_tool",
                "not_connected",
                "Detect PPE, body position, fall, proximity, and restricted-zone events.",
                ("hazard escalation",),
            ),
            EvidenceItem(
                "zone_geofence",
                "ehs_tool",
                "not_connected",
                "Map frame location to restricted areas, walkways, and machine safety zones.",
                ("exposure classification",),
            ),
            EvidenceItem(
                "ehs_rules",
                "rules_tool",
                "not_connected",
                "Apply deterministic escalation rules for stop, report, or inspect actions.",
                ("stop_and_make_safe", "ehs_report"),
            ),
        ),
    }
    available = set(available_tools)
    return tuple(_with_available_status(item, available) for item in tools.get(mode, ()))


def _with_available_status(item: EvidenceItem, available_tools: set[str]) -> EvidenceItem:
    if item.name not in available_tools:
        return item
    return EvidenceItem(
        name=item.name,
        kind=item.kind,
        status="available",
        purpose=item.purpose,
        required_for=item.required_for,
    )


def _policy_for(mode: str) -> str:
    policies = {
        "maintenance": "Use M400 image as observation only; require asset, telemetry, manual, or log evidence before root cause or scheduling certainty.",
        "iqc": "Use detector or quality-plan evidence before release decisions; route uncertain pass claims to quality review.",
        "changeover": "Require machine, SKU, checklist, and first-piece evidence before restart or completion.",
        "wi": "Require machine identity and released WI source before guided operation becomes trusted.",
        "hazard": "Use deterministic safety escalation when exposure evidence is missing or severe.",
    }
    return policies.get(mode, "Use available evidence only and request human confirmation when context is uncertain.")
