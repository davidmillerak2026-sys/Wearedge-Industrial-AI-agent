from __future__ import annotations

import json
from typing import Any

import requests


def call_wearedge_decision_api(
    *,
    agent_host: str,
    agent_port: int,
    api_key_ref: str | None,
    plant_id: str,
    line_id: str,
    equipment_signal_context: dict[str, Any],
    quality_context: dict[str, Any],
    energy_context: dict[str, Any],
    mes_order_context: dict[str, Any],
    workflow_canvas_context: dict[str, Any],
    timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    base_url = f"http://{agent_host}:{agent_port}"
    headers = {"Content-Type": "application/json"}
    if api_key_ref:
        headers["Authorization"] = f"Bearer {api_key_ref}"

    payload = {
        "stage": "final",
        "selected_directions": [
            "maintenance",
            "quality",
            "energy",
            "flexible_production",
            "workflow_canvas",
        ],
        "context": {
            "maintenance": equipment_signal_context,
            "quality": quality_context,
            "energy": energy_context,
            "production": mes_order_context,
            "workflow_canvas": {
                **workflow_canvas_context,
                "plant_id": plant_id,
                "line_id": line_id,
            },
        },
    }

    try:
        response = requests.post(
            f"{base_url}/v1/workflow-canvas/decision",
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        decision = response.json()
        collaborative = decision.get("collaborative_decision", {})
        return {
            "decision_json": decision,
            "primary_direction": collaborative.get("primary_direction", ""),
            "requires_human_confirmation": bool(collaborative.get("requires_human_confirmation", True)),
            "error_message": "",
        }
    except Exception as exc:  # WFC function blocks should return errors, not hide them.
        return {
            "decision_json": {},
            "primary_direction": "",
            "requires_human_confirmation": True,
            "error_message": str(exc),
        }
