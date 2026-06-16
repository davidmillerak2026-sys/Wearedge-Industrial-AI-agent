from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_stable_wearedge_endpoint.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_stable_wearedge_endpoint", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_classifies_temporary_tunnel_as_not_stable() -> None:
    module = _load_module()

    result = module.classify_endpoint("https://quick-cats-study.loca.lt")

    assert result["https"] is True
    assert result["temporary_marker_detected"] is True
    assert result["evidence_tier"] == "temporary_or_local"


def test_verify_passes_stable_https_contract(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"selected_directions": ["maintenance"]}), encoding="utf-8")
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.method, request.full_url, timeout))
        if request.full_url.endswith("/healthz"):
            return FakeResponse(200, {"ok": True})
        if request.full_url.endswith("/v1/edge/runtime-profile"):
            return FakeResponse(200, {"ok": True, "workflow_canvas_ready": True})
        if request.full_url.endswith("/v1/workflow-canvas/decision"):
            return FakeResponse(
                200,
                {
                    "ok": True,
                    "competition_metrics": {"latency_target_met": True},
                    "collaborative_decision": {"primary_direction": "maintenance"},
                },
            )
        raise AssertionError(request.full_url)

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    result = module.verify("https://wearedge.example.com", payload_path)

    assert result["ready"] is True
    assert result["failures"] == []
    assert result["endpoint"]["evidence_tier"] == "stable_https"
    assert [call[0] for call in calls] == ["GET", "GET", "POST"]


def test_verify_flags_temporary_endpoint_even_when_api_contract_passes(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"selected_directions": ["maintenance"]}), encoding="utf-8")

    def fake_urlopen(request, timeout):
        if request.full_url.endswith("/v1/edge/runtime-profile"):
            return FakeResponse(200, {"workflow_canvas_ready": True})
        if request.full_url.endswith("/v1/workflow-canvas/decision"):
            return FakeResponse(200, {"ok": True, "competition_metrics": {"latency_target_met": True}})
        return FakeResponse(200, {"ok": True})

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    result = module.verify("https://demo.trycloudflare.com", payload_path)

    assert result["ready"] is False
    assert "endpoint is not stable HTTPS; use only as temporary PoC evidence" in result["failures"]
