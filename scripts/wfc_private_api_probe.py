from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://wfc.bd-iiot.com"
DEFAULT_SPIDR_URL = "https://spidr.wfc.bd-iiot.com"
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "submission-assets"
    / "live-evidence"
    / "gongyi-mofang"
    / "private-api-probe"
)

ALL_PROBES = (
    "project-files",
    "workflow-api",
    "workflow-json",
    "global-data-table",
    "project-files-dir",
    "dashboard-explorer",
)


@dataclass(frozen=True)
class ProbeRequest:
    name: str
    method: str
    url: str
    output_name: str
    note: str

    def public_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "method": self.method,
            "url": self.url,
            "output_name": self.output_name,
            "note": self.note,
        }


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if not normalized.startswith(("http://", "https://")):
        raise ValueError("base url must start with http:// or https://")
    return normalized


def expand_probes(probes: list[str], workflow_instance_id: str | None = None) -> list[str]:
    selected: list[str] = []
    requested = probes or ["all"]
    for probe in requested:
        if probe == "all":
            selected.extend(ALL_PROBES)
            if workflow_instance_id:
                selected.append("log-manager-page")
        else:
            selected.append(probe)

    unique: list[str] = []
    for probe in selected:
        if probe not in unique:
            unique.append(probe)
    return unique


def build_probe_requests(
    project_id: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    probes: list[str] | None = None,
    workflow_instance_id: str | None = None,
    spidr_url: str = DEFAULT_SPIDR_URL,
) -> list[ProbeRequest]:
    base = normalize_base_url(base_url)
    project_id = project_id.strip()
    if not project_id:
        raise ValueError("project id is required")

    selected = expand_probes(probes or ["all"], workflow_instance_id=workflow_instance_id)
    query = urllib.parse.urlencode(
        {
            "path": spidr_url,
            "workflowInstanceId": workflow_instance_id or "",
        }
    )
    catalog: dict[str, ProbeRequest] = {
        "project-files": ProbeRequest(
            name="project-files",
            method="GET",
            url=f"{base}/api/persistence/files/projects/{quote_path(project_id)}",
            output_name="project-files.json",
            note="List project persistence files if the authenticated session is allowed.",
        ),
        "workflow-json": ProbeRequest(
            name="workflow-json",
            method="GET",
            url=f"{base}/uploads/projects/{quote_path(project_id)}/workflow.json",
            output_name="workflow.json",
            note="Legacy guessed workflow JSON path; keep for diagnosis only.",
        ),
        "workflow-api": ProbeRequest(
            name="workflow-api",
            method="GET",
            url=f"{base}/api/persistence/workflow?{urllib.parse.urlencode({'projectId': project_id, 'workflowId': 'workflow1'})}",
            output_name="workflow-api.json",
            note="Read the frontend-observed workflow persistence API for backup/diagnosis only.",
        ),
        "global-data-table": ProbeRequest(
            name="global-data-table",
            method="GET",
            url=f"{base}/uploads/projects/{quote_path(project_id)}/globalDataTable.json",
            output_name="globalDataTable.json",
            note="Read global data-table definitions for backup/diagnosis only.",
        ),
        "project-files-dir": ProbeRequest(
            name="project-files-dir",
            method="GET",
            url=f"{base}/api/persistence/files/projects/{quote_path(project_id)}/files",
            output_name="project-files-dir.json",
            note="List project uploaded files, function-block files, or related assets if exposed.",
        ),
        "dashboard-explorer": ProbeRequest(
            name="dashboard-explorer",
            method="GET",
            url=f"{base}/api/projects/dashboard-explorer",
            output_name="dashboard-explorer.json",
            note="Read Dashboard Explorer records; an empty response explains the No Dashboard page.",
        ),
    }
    if workflow_instance_id:
        catalog["log-manager-page"] = ProbeRequest(
            name="log-manager-page",
            method="GET",
            url=f"{base}/log-manager/?{query}",
            output_name="log-manager-page.html",
            note="Open the log-manager page for the workflow instance; use as page evidence, not as an API contract.",
        )

    unknown = [probe for probe in selected if probe not in catalog]
    if unknown:
        raise ValueError(f"unknown probe(s): {', '.join(unknown)}")
    return [catalog[probe] for probe in selected]


def quote_path(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def build_auth_headers(cookie_env: str, csrf_token_env: str | None) -> tuple[dict[str, str], dict[str, Any]]:
    cookie = os.environ.get(cookie_env, "")
    headers: dict[str, str] = {
        "Accept": "application/json,text/plain,*/*",
        "User-Agent": "Wearedge-WFC-ReadOnly-Probe/0.1",
    }
    if cookie:
        headers["Cookie"] = cookie

    csrf_set = False
    if csrf_token_env:
        csrf_token = os.environ.get(csrf_token_env, "")
        csrf_set = bool(csrf_token)
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

    auth_status = {
        "cookie_env": cookie_env,
        "cookie_env_set": bool(cookie),
        "csrf_token_env": csrf_token_env,
        "csrf_token_env_set": csrf_set,
    }
    return headers, auth_status


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        lowered = key.lower()
        if lowered in {"cookie", "authorization", "x-csrf-token"}:
            redacted[key] = "<set>" if value else "<empty>"
        else:
            redacted[key] = value
    return redacted


def build_dry_run_result(
    requests: list[ProbeRequest],
    *,
    project_id: str,
    base_url: str,
    auth_status: dict[str, Any],
    headers: dict[str, str],
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "ok": True,
        "mode": "dry-run",
        "project_id": project_id,
        "base_url": normalize_base_url(base_url),
        "output_dir": str(output_dir),
        "auth": auth_status,
        "headers": redact_headers(headers),
        "requests": [request.public_dict() for request in requests],
        "safety": [
            "No network request was made.",
            "No credential value is printed.",
            "Use read-only probes first; do not use private write endpoints as submission evidence.",
        ],
    }


def run_read_only_probes(
    requests: list[ProbeRequest],
    *,
    headers: dict[str, str],
    output_dir: Path,
    timeout: float = 20.0,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for probe in requests:
        results.append(execute_probe(probe, headers=headers, output_dir=output_dir, timeout=timeout))
    return {
        "ok": all(result.get("ok") is True for result in results),
        "mode": "read-only",
        "output_dir": str(output_dir),
        "results": results,
    }


def execute_probe(
    probe: ProbeRequest,
    *,
    headers: dict[str, str],
    output_dir: Path,
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(probe.url, headers=headers, method=probe.method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            status = response.status
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:500]
        return {
            "name": probe.name,
            "ok": False,
            "status": exc.code,
            "url": probe.url,
            "error": f"HTTP {exc.code}",
            "body_preview": error_body,
            "note": probe.note,
        }
    except urllib.error.URLError as exc:
        return {
            "name": probe.name,
            "ok": False,
            "status": None,
            "url": probe.url,
            "error": str(exc.reason),
            "note": probe.note,
        }

    saved_path = save_body(output_dir / probe.output_name, body, content_type)
    return {
        "name": probe.name,
        "ok": True,
        "status": status,
        "url": probe.url,
        "content_type": content_type,
        "bytes": len(body),
        "saved_path": str(saved_path),
        "note": probe.note,
    }


def save_body(path: Path, body: bytes, content_type: str) -> Path:
    text = body.decode("utf-8", errors="replace")
    path.parent.mkdir(parents=True, exist_ok=True)
    if "json" in content_type.lower() or path.suffix.lower() == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            path.write_text(text, encoding="utf-8")
        else:
            path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        path.write_text(text, encoding="utf-8")
    return path


def render_text_summary(result: dict[str, Any]) -> str:
    lines = [
        f"mode={result.get('mode')}",
        f"ok={result.get('ok')}",
        f"output_dir={result.get('output_dir')}",
    ]
    if result.get("mode") == "dry-run":
        auth = result.get("auth", {})
        lines.append(f"cookie_env={auth.get('cookie_env')} set={auth.get('cookie_env_set')}")
        for request in result.get("requests", []):
            lines.append(f"{request['method']} {request['url']} -> {request['output_name']}")
    else:
        for item in result.get("results", []):
            status = item.get("status")
            saved = item.get("saved_path", "")
            error = item.get("error", "")
            lines.append(f"{item.get('name')}: ok={item.get('ok')} status={status} {saved or error}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Gongyi Mofang WFC private API probe for backup and diagnosis."
    )
    parser.add_argument("--project-id", required=True, help="WFC project id, e.g. cmq6lbb9x00bx1l6pxll7voae.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--probe",
        action="append",
        choices=(*ALL_PROBES, "log-manager-page", "all"),
        default=None,
        help="Probe to run. Repeatable. Default: all.",
    )
    parser.add_argument("--workflow-instance-id", default=None)
    parser.add_argument("--spidr-url", default=DEFAULT_SPIDR_URL)
    parser.add_argument("--cookie-env", default="WFC_COOKIE")
    parser.add_argument("--csrf-token-env", default="WFC_CSRF_TOKEN")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--dry-run", action="store_true", help="Print planned GET requests without network I/O.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args(argv)

    try:
        requests = build_probe_requests(
            args.project_id,
            base_url=args.base_url,
            probes=args.probe or ["all"],
            workflow_instance_id=args.workflow_instance_id,
            spidr_url=args.spidr_url,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    headers, auth_status = build_auth_headers(args.cookie_env, args.csrf_token_env)

    if args.dry_run:
        result = build_dry_run_result(
            requests,
            project_id=args.project_id,
            base_url=args.base_url,
            auth_status=auth_status,
            headers=headers,
            output_dir=args.output_dir,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text_summary(result))
        return 0

    if not auth_status["cookie_env_set"]:
        print(
            f"ERROR: {args.cookie_env} is not set. Refusing private WFC requests without an explicit session cookie.",
            file=sys.stderr,
        )
        return 2

    result = run_read_only_probes(requests, headers=headers, output_dir=args.output_dir, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text_summary(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
