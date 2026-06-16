from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = REPO_ROOT / "workflows" / "wearedge_wfc_poc_payload.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "stable-endpoint"
TEMPORARY_HOST_MARKERS = (
    "loca.lt",
    "trycloudflare.com",
    "ngrok-free.app",
    "ngrok.io",
    "localhost",
    "127.0.0.1",
)


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def normalize_base_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value.strip())
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("base url must include scheme and host, e.g. https://agent.example.com")
    return value.strip().rstrip("/")


def call_json(method: str, url: str, payload: dict[str, Any] | None = None, token: str | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return {"ok": True, "status": response.status, "json": json.loads(raw)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": exc.read().decode("utf-8", errors="replace")[:500]}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def classify_endpoint(base_url: str) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(base_url)
    host = parsed.hostname or ""
    temporary = any(marker in host for marker in TEMPORARY_HOST_MARKERS)
    return {
        "scheme": parsed.scheme,
        "host": host,
        "https": parsed.scheme == "https",
        "temporary_marker_detected": temporary,
        "evidence_tier": "stable_https" if parsed.scheme == "https" and not temporary else "temporary_or_local",
    }


def verify(base_url: str, payload_path: Path, token: str | None = None) -> dict[str, Any]:
    base_url = normalize_base_url(base_url)
    endpoint = classify_endpoint(base_url)
    payload = load_payload(payload_path)
    checks = {
        "healthz": call_json("GET", f"{base_url}/healthz", token=token),
        "runtime_profile": call_json("GET", f"{base_url}/v1/edge/runtime-profile", token=token),
        "workflow_canvas_decision": call_json(
            "POST",
            f"{base_url}/v1/workflow-canvas/decision",
            payload=payload,
            token=token,
        ),
    }
    failures = []
    for name, result in checks.items():
        if not result.get("ok"):
            failures.append(f"{name}: request failed")
    decision = checks["workflow_canvas_decision"].get("json") or {}
    profile = checks["runtime_profile"].get("json") or {}
    if decision.get("ok") is not True:
        failures.append("workflow decision ok must be true")
    if (decision.get("competition_metrics") or {}).get("latency_target_met") is not True:
        failures.append("workflow decision latency target must be met")
    if profile.get("workflow_canvas_ready") is not True:
        failures.append("runtime profile workflow_canvas_ready must be true")
    if endpoint["evidence_tier"] != "stable_https":
        failures.append("endpoint is not stable HTTPS; use only as temporary PoC evidence")
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "base_url": base_url,
        "endpoint": endpoint,
        "ready": not failures,
        "failures": failures,
        "checks": checks,
        "boundary": (
            "This verifier confirms external endpoint reachability and API contract. "
            "It does not publish an Xcelerator service or prove a production deployment."
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# Stable Wearedge Endpoint Evidence",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Base URL: `{result['base_url']}`",
        f"- Evidence tier: `{result['endpoint']['evidence_tier']}`",
        f"- Ready: {result['ready']}",
        "",
        "## Checks",
        "",
        "| Check | OK | HTTP Status |",
        "| --- | --- | ---: |",
    ]
    for name, check in result["checks"].items():
        lines.append(f"| {name} | {check.get('ok')} | {check.get('status')} |")
    lines += ["", "## Failures", ""]
    lines += [f"- {failure}" for failure in result["failures"]] or ["- None"]
    lines += ["", "## Boundary", "", result["boundary"], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a stable HTTPS Wearedge API endpoint for Xcelerator/WFC PoC.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--payload", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument("--token", default=None, help="Optional bearer token; do not put secrets in files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write-evidence", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = verify(args.base_url, args.payload, args.token)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.write_evidence:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "stable-endpoint-evidence.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (args.output_dir / "stable-endpoint-evidence.md").write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_report(result))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
