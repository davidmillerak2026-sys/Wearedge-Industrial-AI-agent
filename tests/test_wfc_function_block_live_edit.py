import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WFC_FB_PATH = REPO_ROOT / "workflows" / "wfc_call_wearedge_decision_fb_main.py"


def load_wfc_fb_module():
    spec = importlib.util.spec_from_file_location("wfc_call_wearedge_decision_fb_main", WFC_FB_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_wfc_function_block_outputs_compact_summary(monkeypatch):
    module = load_wfc_fb_module()
    calls = []

    response_body = {
        "ok": True,
        "latency_ms": 12,
        "competition_metrics": {
            "decision_accuracy_pct_estimate": 97.0,
            "latency_target_met": True,
            "final_min_agent_directions_met": True,
        },
        "collaborative_decision": {
            "primary_direction": "maintenance",
            "priority": "high",
            "recommendation": "Create maintenance work order and confirm bearing signal.",
            "requires_human_confirmation": True,
            "required_confirmations": ["machine identity", "maintenance engineer approval"],
            "residual_risk": "human_confirmation_required_before_ot_control",
        },
        "workflow_canvas": {
            "function_blocks": [
                "WearedgeAgentServiceResource",
                "CallWearedgeDecisionApi",
                "HumanApprovalGate",
            ]
        },
        "evaluations": [{"large": "field that should not be copied into WFC output1"}],
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(response_body).encode("utf-8")

    def fake_urlopen(request, timeout, context):
        calls.append(
            {
                "url": request.full_url,
                "timeout": timeout,
                "headers": dict(request.header_items()),
                "body": json.loads(request.data.decode("utf-8")),
            }
        )
        return FakeResponse()

    outputs = []
    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    block = module.FunctionBlock(
        {
            "input1": json.dumps({"baseUrl": "https://agent.example"}),
            "input2": json.dumps({"selected_directions": ["maintenance"]}),
        },
        outputs.append,
        lambda *_args, **_kwargs: None,
        lambda *_args, **_kwargs: None,
        lambda *_args, **_kwargs: None,
    )

    block.run()

    assert calls[0]["url"] == "https://agent.example/v1/workflow-canvas/decision"
    assert calls[0]["timeout"] == 15
    assert calls[0]["headers"]["Content-type"] == "application/json"
    assert calls[0]["headers"]["Bypass-tunnel-reminder"] == "1"
    assert calls[0]["body"]["selected_directions"] == ["maintenance"]

    assert len(outputs) == 1
    output = outputs[0]
    summary = json.loads(output.output1)
    assert output.status == "Good"
    assert output.ok is True
    assert output.latency_ms == 12
    assert output.selected_direction == "maintenance"
    assert output.approval_status == "pending"
    assert summary["ok"] is True
    assert summary["latency_ms"] == 12
    assert summary["selected_direction"] == "maintenance"
    assert summary["competition_metrics"]["decision_accuracy_pct_estimate"] == 97.0
    assert summary["workflow_function_blocks"] == [
        "WearedgeAgentServiceResource",
        "CallWearedgeDecisionApi",
        "HumanApprovalGate",
    ]
    assert "evaluations" not in summary
