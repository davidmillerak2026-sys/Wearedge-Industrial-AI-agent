from __future__ import annotations

from fastapi.testclient import TestClient

import jetson.app as app_module
from jetson.config import GatewayConfig

from test_competition_decision import _competition_payload


def _x_auth_config() -> GatewayConfig:
    return GatewayConfig(
        llama_base_url="http://127.0.0.1:8080",
        model="gemma4",
        demo_token=None,
        max_image_mb=4,
        enable_thinking=False,
        max_tokens=160,
        temperature=0.0,
        timeout_seconds=10,
        upload_dir=None,
        event_log_path=None,
        auth_disabled=False,
        contract_min_words=16,
        contract_repair_enabled=True,
        llama_image_min_tokens=560,
        llama_image_max_tokens=560,
        audio_fusion_runtime="llama.cpp",
        model_variant="E2B",
        xcelerator_x_auth_enabled=True,
        xcelerator_app_key="demo-app-id",
        xcelerator_sign_check_url="https://apig.developers.siemens-x.com.cn/x-api/sign/check",
        xcelerator_sign_check_timeout_seconds=1,
    )


def test_workflow_canvas_decision_accepts_valid_xcelerator_token(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "config", _x_auth_config())
    seen_tokens: list[str] = []

    def fake_verify(token: str) -> bool:
        seen_tokens.append(token)
        return True

    monkeypatch.setattr(app_module, "_verify_xcelerator_token", fake_verify)

    response = TestClient(app_module.app).post(
        "/v1/workflow-canvas/decision",
        headers={"X-TOKEN": "valid-x-token"},
        json=_competition_payload(),
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert seen_tokens == ["valid-x-token"]


def test_workflow_canvas_decision_rejects_invalid_xcelerator_token(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "config", _x_auth_config())
    monkeypatch.setattr(app_module, "_verify_xcelerator_token", lambda token: False)

    response = TestClient(app_module.app).post(
        "/v1/workflow-canvas/decision",
        headers={"X-TOKEN": "invalid-x-token"},
        json=_competition_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid Xcelerator X-TOKEN"
