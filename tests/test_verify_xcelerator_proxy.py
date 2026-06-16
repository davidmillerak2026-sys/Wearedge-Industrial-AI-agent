from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_xcelerator_proxy.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_xcelerator_proxy", SCRIPT_PATH)
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


def test_rejects_non_https_proxy_url() -> None:
    module = _load_module()

    try:
        module.normalize_base_url("http://apig.example.com/path")
    except ValueError as exc:
        assert "https URL" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_verify_passes_when_proxy_returns_wearedge_ok(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"selected_directions": ["maintenance"]}), encoding="utf-8")

    def fake_urlopen(request, timeout):
        if request.full_url.endswith("/v1/workflow-canvas/decision"):
            return FakeResponse(200, {"ok": True, "competition_metrics": {"latency_target_met": True}})
        return FakeResponse(200, {"ok": True})

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    result = module.verify("https://apig.example.com/scps", payload_path)

    assert result["ready"] is True
    assert result["failures"] == []
    assert set(result["checks"]) == {"runtime_profile", "healthz", "workflow_canvas_decision"}


def test_verify_flags_xcelerator_selector_error(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"selected_directions": ["maintenance"]}), encoding="utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse(
            200,
            {
                "code": -107,
                "msg": "divide:Can not find selector, please check your configuration!",
                "bizMessage": None,
            },
        )

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    result = module.verify("https://apig.example.com/scps", payload_path, skip_decision=True)

    assert result["ready"] is False
    assert len(result["failures"]) == 2
    assert all("code -107" in failure for failure in result["failures"])


def test_render_report_includes_platform_signal(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"selected_directions": ["maintenance"]}), encoding="utf-8")

    def fake_urlopen(request, timeout):
        return FakeResponse(200, {"code": -107, "msg": "divide:Can not find selector"})

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    report = module.render_report(module.verify("https://apig.example.com/scps", payload_path, skip_decision=True))

    assert "platform code=-107" in report
    assert "selector configuration" in report
