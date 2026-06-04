from __future__ import annotations

from dataclasses import dataclass

from .evidence_plan import EvidencePlan


TOOL_PLAN_VERSION = "wear-edge-tool-plan.v1"
DEFAULT_MAX_TOOL_CALLS = 3


@dataclass(frozen=True)
class ToolSkip:
    name: str
    kind: str
    reason: str
    required_for: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "reason": self.reason,
            "required_for": list(self.required_for),
        }


@dataclass(frozen=True)
class BoundedToolPlan:
    version: str
    mode: str
    max_iterations: int
    max_tool_calls: int
    used_tool_calls: int
    status: str
    selected_tools: tuple[str, ...]
    skipped_tools: tuple[ToolSkip, ...]
    deferred_tools: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "mode": self.mode,
            "max_iterations": self.max_iterations,
            "max_tool_calls": self.max_tool_calls,
            "used_tool_calls": self.used_tool_calls,
            "status": self.status,
            "selected_tools": list(self.selected_tools),
            "skipped_tools": [item.as_dict() for item in self.skipped_tools],
            "deferred_tools": list(self.deferred_tools),
        }


def build_bounded_tool_plan(
    evidence_plan: EvidencePlan,
    *,
    max_iterations: int = 1,
    max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
) -> BoundedToolPlan:
    planned_tools = evidence_plan.planned_tools
    selected = planned_tools[:max_tool_calls]
    deferred = tuple(item.name for item in planned_tools[max_tool_calls:])
    skipped = tuple(
        ToolSkip(
            name=item.name,
            kind=item.kind,
            reason="not_connected" if item.status == "not_connected" else "not_available",
            required_for=item.required_for,
        )
        for item in selected
        if item.status != "available"
    )
    used_tool_calls = sum(1 for item in selected if item.status == "available")
    status = "ready"
    if skipped:
        status = "missing_tool_connections"
    elif not selected:
        status = "no_tools_required"
    return BoundedToolPlan(
        version=TOOL_PLAN_VERSION,
        mode=evidence_plan.mode,
        max_iterations=max_iterations,
        max_tool_calls=max_tool_calls,
        used_tool_calls=used_tool_calls,
        status=status,
        selected_tools=tuple(item.name for item in selected),
        skipped_tools=skipped,
        deferred_tools=deferred,
    )


def build_tool_prompt_context(plan: BoundedToolPlan) -> str:
    selected = ", ".join(plan.selected_tools) if plan.selected_tools else "none"
    skipped = ", ".join(item.name for item in plan.skipped_tools) if plan.skipped_tools else "none"
    deferred = ", ".join(plan.deferred_tools) if plan.deferred_tools else "none"
    return (
        "Bounded tool context:\n"
        f"- budget={plan.max_iterations} iteration/{plan.max_tool_calls} calls; selected={selected}; used={plan.used_tool_calls}.\n"
        f"- skipped={skipped}; deferred={deferred}.\n"
        "Do not present skipped/deferred tools as evidence."
    )


def build_tool_action_logs(plan: BoundedToolPlan) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "stage": "bounded_react_tools",
            "action_type": "tool_call",
            "status": "skipped",
            "tool": item.name,
            "tool_kind": item.kind,
            "reason": item.reason,
            "required_for": list(item.required_for),
        }
        for item in plan.skipped_tools
    )
