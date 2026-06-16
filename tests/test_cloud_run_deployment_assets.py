from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cloud_run_dockerfile_uses_cloud_run_port_and_no_secret_defaults() -> None:
    dockerfile = (REPO_ROOT / "Dockerfile.cloudrun").read_text(encoding="utf-8")

    assert "uvicorn jetson.app:app" in dockerfile
    assert "--port ${PORT:-8080}" in dockerfile
    assert "WEAREDGE_DEPLOYMENT_MODE=cloud_proxy" in dockerfile
    assert "DEMO_TOKEN" not in dockerfile
    assert "WEAREDGE_XCELERATOR_APP_KEY" not in dockerfile


def test_cloud_run_runbook_matches_stable_endpoint_verifier_contract() -> None:
    runbook = (REPO_ROOT / "deploy" / "cloud-run" / "README.md").read_text(encoding="utf-8")

    assert "/healthz" in runbook
    assert "/v1/edge/runtime-profile" in runbook
    assert "/v1/workflow-canvas/decision" in runbook
    assert "verify_stable_wearedge_endpoint.py" in runbook
    assert "Allow unauthenticated" in runbook or "unauthenticated" in runbook


def test_cloud_build_uses_cloud_run_dockerfile() -> None:
    cloudbuild = (REPO_ROOT / "deploy" / "cloud-run" / "cloudbuild.yaml").read_text(encoding="utf-8")
    deploy_script = (REPO_ROOT / "deploy" / "cloud-run" / "cloud-shell-deploy.sh").read_text(encoding="utf-8")

    assert "Dockerfile.cloudrun" in cloudbuild
    assert "gcloud builds submit" in deploy_script
    assert "gcloud run deploy" in deploy_script
    assert "--allow-unauthenticated" in deploy_script
    assert "WEAREDGE_DEPLOYMENT_MODE=cloud_proxy" in deploy_script
