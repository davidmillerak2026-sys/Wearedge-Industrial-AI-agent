from __future__ import annotations

import json

from jetson.audit_log import append_jsonl, read_recent_jsonl
from jetson.app import _agent_run_summary


def test_append_jsonl_creates_parent_and_writes_one_event(tmp_path) -> None:
    path = tmp_path / "events" / "inference.jsonl"
    append_jsonl(path, {"request_id": "abc123", "scene": "设备间"})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"request_id": "abc123", "scene": "设备间"}


def test_read_recent_jsonl_returns_newest_first_and_skips_bad_lines(tmp_path) -> None:
    path = tmp_path / "inference.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"request_id": "oldest"}),
                "{bad json",
                json.dumps({"request_id": "middle"}),
                json.dumps({"request_id": "newest"}),
            ]
        ),
        encoding="utf-8",
    )

    events = read_recent_jsonl(path, limit=2)

    assert [event["request_id"] for event in events] == ["newest", "middle"]


def test_read_recent_jsonl_missing_file_returns_empty_list(tmp_path) -> None:
    assert read_recent_jsonl(tmp_path / "missing.jsonl", limit=10) == []


def test_agent_run_summary_keeps_runtime_stream_and_last_event() -> None:
    event = {
        "event_type": "inference.completed",
        "request_id": "req-001",
        "analysis_mode": "iqc",
        "received_at": "2026-05-13T00:00:00Z",
        "runtime_stream": {
            "version": "wear-edge-runtime-stream.v1",
            "events": [
                {"sequence": 1, "event": "workflow.stage.completed"},
                {"sequence": 2, "event": "workflow.closed"},
            ],
        },
        "action_card": {"channel": "quality_hold"},
        "integration_event": {"target": "qms_quality_event"},
    }

    summary = _agent_run_summary(event)

    assert summary["request_id"] == "req-001"
    assert summary["analysis_mode"] == "iqc"
    assert summary["runtime_stream"] == event["runtime_stream"]
    assert summary["last_event"] == {"sequence": 2, "event": "workflow.closed"}
    assert summary["action_card"] == {"channel": "quality_hold"}
