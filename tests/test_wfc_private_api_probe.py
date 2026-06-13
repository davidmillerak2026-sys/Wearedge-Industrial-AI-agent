from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wfc_private_api_probe.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("wfc_private_api_probe", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_probe_requests_includes_known_wfc_paths() -> None:
    module = _load_module()

    requests = module.build_probe_requests(
        "cmq6lbb9x00bx1l6pxll7voae",
        probes=["all"],
        workflow_instance_id="ryn.cmq6lbb9x00bx1l6pxll7voae.workflow1",
    )

    urls = {request.name: request.url for request in requests}
    assert urls["project-files"].endswith("/api/persistence/files/projects/cmq6lbb9x00bx1l6pxll7voae")
    assert urls["workflow-api"].endswith(
        "/api/persistence/workflow?projectId=cmq6lbb9x00bx1l6pxll7voae&workflowId=workflow1"
    )
    assert urls["workflow-json"].endswith("/uploads/projects/cmq6lbb9x00bx1l6pxll7voae/workflow.json")
    assert urls["global-data-table"].endswith(
        "/uploads/projects/cmq6lbb9x00bx1l6pxll7voae/globalDataTable.json"
    )
    assert urls["dashboard-explorer"].endswith("/api/projects/dashboard-explorer")
    assert "workflowInstanceId=ryn.cmq6lbb9x00bx1l6pxll7voae.workflow1" in urls["log-manager-page"]


def test_dry_run_redacts_cookie_value(monkeypatch, capsys, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.setenv("WFC_COOKIE", "sessionid=super-secret-cookie")

    exit_code = module.main(
        [
            "--project-id",
            "cmq6lbb9x00bx1l6pxll7voae",
            "--probe",
            "workflow-json",
            "--output-dir",
            str(tmp_path),
            "--dry-run",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exit_code == 0
    assert result["headers"]["Cookie"] == "<set>"
    assert "super-secret-cookie" not in captured.out
    assert result["requests"][0]["url"].endswith(
        "/uploads/projects/cmq6lbb9x00bx1l6pxll7voae/workflow.json"
    )


def test_non_dry_run_requires_explicit_cookie(monkeypatch, capsys, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.delenv("WFC_COOKIE", raising=False)

    exit_code = module.main(
        [
            "--project-id",
            "cmq6lbb9x00bx1l6pxll7voae",
            "--probe",
            "workflow-json",
            "--output-dir",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "WFC_COOKIE is not set" in captured.err
    assert not any(tmp_path.iterdir())


def test_unknown_probe_is_rejected() -> None:
    module = _load_module()

    try:
        module.build_probe_requests("project-1", probes=["private-write"])
    except ValueError as exc:
        assert "unknown probe" in str(exc)
    else:
        raise AssertionError("unknown probe should fail")
