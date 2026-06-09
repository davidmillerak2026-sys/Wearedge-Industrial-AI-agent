from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = REPO_ROOT / "openapi" / "wearedge-xcelerator-apiworld.openapi.json"
RUNBOOK_PATH = REPO_ROOT / "docs" / "xcelerator-apiworld-onboarding.md"


def test_xcelerator_openapi_import_spec_contains_decision_endpoint() -> None:
    spec = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))

    assert spec["openapi"].startswith("3.")
    assert "/v1/workflow-canvas/decision" in spec["paths"]
    assert "/healthz" in spec["paths"]
    decision = spec["paths"]["/v1/workflow-canvas/decision"]["post"]
    assert decision["operationId"] == "buildWorkflowCanvasDecision"
    assert {"XceleratorXToken": []} in decision["security"]
    assert spec["components"]["securitySchemes"]["XceleratorXToken"]["name"] == "X-TOKEN"


def test_xcelerator_runbook_tracks_platform_auth_constraints() -> None:
    text = RUNBOOK_PATH.read_text(encoding="utf-8")

    assert "X-TOKEN" in text
    assert "/x-api/sign/check" in text
    assert "30 秒" in text
    assert "WEAREDGE_XCELERATOR_APP_KEY" in text
    assert "openapi/wearedge-xcelerator-apiworld.openapi.json" in text
