from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "capture_submission_screenshots.py"


def _load_capture_module():
    spec = importlib.util.spec_from_file_location("capture_submission_screenshots", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_markdown_renderer_handles_tables_and_code() -> None:
    module = _load_capture_module()

    rendered = module.render_markdown(
        "\n".join(
            [
                "# Title",
                "",
                "| A | B |",
                "| --- | --- |",
                "| one | `two` |",
                "",
                "```",
                "ok=True",
                "```",
            ]
        )
    )

    assert "<h1>Title</h1>" in rendered
    assert "<table>" in rendered
    assert "<code>two</code>" in rendered
    assert "ok=True" in rendered


def test_capture_plan_has_required_submission_shots() -> None:
    module = _load_capture_module()
    output_names = {spec.output_name for spec in module.DOCUMENT_SPECS}

    assert "01-local-readme.png" in output_names
    assert "03-offline-eval-report.png" in output_names
    assert "05-wfc-payload.png" in output_names
    assert "06-dashboard-mock.png" in output_names
    assert "07-api-schema.png" in output_names
    assert "16-solution-profile.png" in inspect.getsource(module._run_evidence_commands)
