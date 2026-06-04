from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_PAYLOAD = REPO_ROOT / "workflows" / "wearedge_wfc_poc_payload.json"


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def call_in_process(payload: dict[str, Any]) -> dict[str, Any]:
    from jetson.competition import build_competition_decision

    return build_competition_decision(payload)


def call_http(url: str, payload: dict[str, Any], token: str | None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    return json.loads(raw)


def validate_decision(decision: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if decision.get("ok") is not True:
        failures.append("ok must be true")
    metrics = _object(decision.get("competition_metrics"))
    workflow = _object(decision.get("workflow_canvas"))
    collaborative = _object(decision.get("collaborative_decision"))
    if metrics.get("latency_target_met") is not True:
        failures.append("competition_metrics.latency_target_met must be true")
    if "function_blocks" not in workflow:
        failures.append("workflow_canvas.function_blocks missing")
    else:
        blocks = workflow.get("function_blocks")
        if not isinstance(blocks, list) or "CollaborativeDecisionGate" not in blocks:
            failures.append("workflow_canvas.function_blocks must include CollaborativeDecisionGate")
    if collaborative.get("primary_direction") is None:
        failures.append("collaborative_decision.primary_direction missing")
    if "competition_metrics" not in decision:
        failures.append("competition_metrics missing")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test Workflow Canvas decision payload.")
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument(
        "--url",
        default=None,
        help="Optional running gateway endpoint, e.g. http://127.0.0.1:8081/v1/workflow-canvas/decision",
    )
    parser.add_argument("--token", default=None, help="Optional bearer token for HTTP mode.")
    parser.add_argument("--json", action="store_true", help="Print full decision JSON.")
    args = parser.parse_args(argv)

    payload = load_payload(args.payload)
    decision = call_http(args.url, payload, args.token) if args.url else call_in_process(payload)
    failures = validate_decision(decision)
    if args.json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
    else:
        print(f"mode={'http' if args.url else 'in-process'}")
        print(f"ok={decision.get('ok')}")
        print(f"primary_direction={_object(decision.get('collaborative_decision')).get('primary_direction')}")
        print(f"latency_ms={decision.get('latency_ms')}")
        print(f"function_blocks={len(_object(decision.get('workflow_canvas')).get('function_blocks', []))}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
