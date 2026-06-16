from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "analyze_wfc_workflow_bindings.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("analyze_wfc_workflow_bindings", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_analyze_confirms_python_output_to_update_table_connection() -> None:
    module = _load_module()
    workflow = {
        "nodes": [
            {
                "id": "Language.Python.1",
                "displayName": "CallWearedgeDecisionApi",
                "outputs": [{"name": "输出1"}],
            },
            {
                "id": "System.UpdateDataTable.1",
                "displayName": "更新数据表.1",
                "fields": ["selected_direction", "priority", "recommended_action", "approval_status"],
            },
        ],
        "edges": [
            {
                "type": "data",
                "source": "Language.Python.1",
                "sourcePort": "输出1",
                "target": "System.UpdateDataTable.1",
                "targetPort": "输入",
            }
        ],
    }

    result = module.analyze_workflow(workflow)

    assert result["source_block_found"] is True
    assert result["target_block_found"] is True
    assert result["required_fields_missing"] == []
    assert result["confirmed_python_output_to_update_table"] is True
    assert result["candidate_connection_count"] == 1


def test_analyze_marks_missing_dynamic_connection_for_review() -> None:
    module = _load_module()
    workflow = {
        "nodes": [
            {"id": "Language.Python.1", "displayName": "CallWearedgeDecisionApi"},
            {
                "id": "System.UpdateDataTable.1",
                "displayName": "更新数据表.1",
                "staticInputs": {
                    "selected_direction": "maintenance",
                    "priority": "P1",
                    "recommended_action": "Inspect bearing vibration",
                    "approval_status": "pending_human_approval",
                },
            },
        ],
        "edges": [
            {
                "type": "control",
                "source": "Language.Python.1",
                "target": "System.UpdateDataTable.1",
            }
        ],
    }

    result = module.analyze_workflow(workflow)

    assert result["source_block_found"] is True
    assert result["target_block_found"] is True
    assert result["confirmed_python_output_to_update_table"] is False
    assert result["candidate_connection_count"] == 1


def test_cli_json_output(tmp_path: Path, capsys) -> None:
    module = _load_module()
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "Language.Python.1", "displayName": "CallWearedgeDecisionApi"},
                    {"id": "System.UpdateDataTable.1", "displayName": "更新数据表.1"},
                ]
            }
        ),
        encoding="utf-8",
    )

    exit_code = module.main([str(workflow_path), "--json"])

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert exit_code == 0
    assert result["ok"] is True
    assert result["confirmed_python_output_to_update_table"] is False


def test_load_json_rejects_wfc_binary_export(tmp_path: Path) -> None:
    module = _load_module()
    workflow_export = tmp_path / "workflow.wfcw"
    workflow_export.write_bytes(b"\x00\x01binary-wfc-export")

    try:
        module.load_json(workflow_export)
    except ValueError as exc:
        assert "proprietary export file" in str(exc)
        assert "live screenshots" in str(exc)
    else:
        raise AssertionError("expected ValueError")
