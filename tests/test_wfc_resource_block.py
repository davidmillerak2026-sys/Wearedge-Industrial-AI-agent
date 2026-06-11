from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCK_ROOT = REPO_ROOT / "wfc-blocks" / "wearedge-agent-service"


def test_wfc_resource_block_declares_edge_runtime_parameters() -> None:
    info = json.loads((BLOCK_ROOT / "info.json").read_text(encoding="utf-8"))

    assert info["displayName"] == "Wearedge Agent Service"
    assert info["type"] == "wearedge.agent.service"
    parameters = {item["name"]: item for item in info["parameters"]}
    for name in ("agentHost", "agentPort", "apiKeyRef", "deploymentMode", "plantId", "lineId"):
        assert name in parameters
    assert parameters["deploymentMode"]["options"] == ["jetson", "ipc", "local_server", "cloud_proxy"]


def test_wfc_function_block_example_calls_workflow_canvas_endpoint() -> None:
    code = (BLOCK_ROOT / "function-blocks" / "CallWearedgeDecisionApi.py").read_text(encoding="utf-8")

    assert "/v1/workflow-canvas/decision" in code
    assert "HumanApprovalGate" not in code
    assert "requires_human_confirmation" in code


def test_live_wfc_fb_main_reference_is_platform_safe() -> None:
    code = (REPO_ROOT / "workflows" / "wfc_call_wearedge_decision_fb_main.py").read_text(
        encoding="utf-8"
    )

    assert "/v1/workflow-canvas/decision" in code
    assert "wearedge_decision_ok" in code
    assert "urllib.request" in code
    assert "bypass-tunnel-reminder" in code
    assert "apiKey" not in code
    assert "AppSecret" not in code
