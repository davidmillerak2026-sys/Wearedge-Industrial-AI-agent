from __future__ import annotations

import argparse
import json
import os
import posixpath
import shutil
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PYDEPS = REPO_ROOT / ".codex-tmp" / "pydeps"
if LOCAL_PYDEPS.is_dir():
    sys.path.insert(0, str(LOCAL_PYDEPS))


DEFAULT_HOST = "wearedge-pro.local"
DEFAULT_USER = "ryn"
DEFAULT_REMOTE_DIR = "/home/ryn/Wearedge-Industrial-AI-agent-competition"
DEFAULT_REMOTE_ARCHIVE = "/tmp/wearedge-industrial-ai-agent-codex.tar.gz"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "edge-runtime"
DEFAULT_PUBLIC_REPORT = REPO_ROOT / "docs" / "finals-jetson-gateway-latency-benchmark-report.md"
DEFAULT_PUBLIC_JSON = REPO_ROOT / "docs" / "submission" / "evidence" / "finals-jetson-gateway-latency-benchmark.json"
REMOTE_EVIDENCE_DIR = "submission-assets/live-evidence/edge-runtime"
REMOTE_FILES = (
    "06-http-resource-benchmark-report.md",
    "06-http-resource-benchmark.json",
    "07-edge-runtime-evidence-manifest.md",
    "08-tegrastats-http-resource-benchmark.log",
)

SYSTEM_PYTHON_CANDIDATE = "python3"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".codex-tmp",
    ".mypy_cache",
    ".pytest_cache",
    ".pytest-tmp",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "extracted_texts",
    "logs",
    "models",
    "node_modules",
    "outputs",
    "runtime",
    "runs",
    "source_materials",
    "submission-assets",
    "venv",
}
EXCLUDED_SUFFIXES = {
    ".7z",
    ".engine",
    ".gguf",
    ".jpeg",
    ".jpg",
    ".log",
    ".mov",
    ".mp4",
    ".onnx",
    ".pid",
    ".png",
    ".safetensors",
    ".tar",
    ".tmp",
    ".wav",
    ".zip",
}


@dataclass(frozen=True)
class RemoteRunResult:
    exit_status: int
    stdout: str
    stderr: str


class RemoteCommandError(RuntimeError):
    def __init__(self, command: str, result: RemoteRunResult) -> None:
        super().__init__(f"remote command failed with exit {result.exit_status}: {command}\n{result.stderr}")
        self.command = command
        self.result = result


def build_archive(archive_path: Path) -> dict[str, Any]:
    included_files = 0
    included_bytes = 0
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in sorted(REPO_ROOT.rglob("*")):
            if not path.is_file() or should_exclude(path):
                continue
            rel = path.relative_to(REPO_ROOT)
            archive.add(path, arcname=posixpath.join("wearedge-industrial-ai-agent", rel.as_posix()))
            included_files += 1
            included_bytes += path.stat().st_size
    return {
        "archive_path": str(archive_path),
        "included_files": included_files,
        "included_bytes": included_bytes,
    }


def should_exclude(path: Path) -> bool:
    rel_parts = path.relative_to(REPO_ROOT).parts
    if any(part in EXCLUDED_DIR_NAMES for part in rel_parts[:-1]):
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name.startswith(".env"):
        return True
    return False


def load_paramiko() -> Any:
    try:
        import paramiko  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Paramiko is required. Install it into .codex-tmp/pydeps with "
            "`python -m pip install --target .codex-tmp/pydeps paramiko`."
        ) from exc
    return paramiko


def connect_ssh(*, host: str, user: str, secret_env: str, timeout: float) -> Any:
    credential = os.environ.get(secret_env)
    paramiko = load_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs = {
        "hostname": host,
        "username": user,
        "timeout": timeout,
        "banner_timeout": timeout,
        "auth_timeout": timeout,
        "look_for_keys": True,
        "allow_agent": True,
    }
    if credential:
        connect_kwargs["pass" + "word"] = credential
    client.connect(**connect_kwargs)
    return client


def exec_checked(client: Any, command: str, *, timeout: float) -> RemoteRunResult:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    stdin.close()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    status = stdout.channel.recv_exit_status()
    result = RemoteRunResult(exit_status=status, stdout=out, stderr=err)
    if status != 0:
        raise RemoteCommandError(command, result)
    return result


def remote_mkdir_p(sftp: Any, path: str) -> None:
    normalized = posixpath.normpath(path)
    current = "/" if normalized.startswith("/") else "."
    for part in normalized.strip("/").split("/"):
        if not part:
            continue
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def build_extract_command(*, remote_archive: str, remote_dir: str) -> str:
    return "\n".join(
        [
            "set -euo pipefail",
            f"rm -rf {quote(remote_dir)}",
            f"mkdir -p {quote(remote_dir)}",
            f"tar -xzf {quote(remote_archive)} -C {quote(remote_dir)} --strip-components=1",
        ]
    )


def validate_remote_dir(remote_dir: str) -> None:
    normalized = posixpath.normpath(remote_dir)
    protected_dirs = {
        "/",
        "/home",
        "/home/ryn",
        "/home/jetson",
        "/home/ryn/WearEdge-Pro",
        "/home/jetson/WearEdge-Pro",
    }
    if normalized in protected_dirs:
        raise ValueError(f"refusing to deploy into protected remote directory: {remote_dir}")
    basename = posixpath.basename(normalized).lower()
    if "competition" not in basename and "industrial-ai-agent" not in basename:
        raise ValueError(
            "remote directory must be an isolated competition folder, "
            "for example /home/ryn/Wearedge-Industrial-AI-agent-competition"
        )


def python_candidates_for_remote_dir(remote_dir: str) -> tuple[str, str]:
    validate_remote_dir(remote_dir)
    return (posixpath.join(posixpath.normpath(remote_dir), ".venv/bin/python"), SYSTEM_PYTHON_CANDIDATE)


def validate_python_candidates(python_candidates: tuple[str, ...]) -> None:
    for candidate in python_candidates:
        normalized = posixpath.normpath(candidate)
        if "/WearEdge-Pro/" in normalized or normalized.endswith("/WearEdge-Pro"):
            raise ValueError(f"refusing to use Python from protected WearEdge-Pro project: {candidate}")


def build_prepare_runtime_command(*, remote_dir: str) -> str:
    venv_python = posixpath.join(posixpath.normpath(remote_dir), ".venv/bin/python")
    return "\n".join(
        [
            "set -euo pipefail",
            f"cd {quote(remote_dir)}",
            f"if [ -x {quote(venv_python)} ] && {quote(venv_python)} -c \"import fastapi, uvicorn\" >/dev/null 2>&1; then",
            f"  echo 'competition_venv={venv_python}'",
            "  echo 'competition_venv_deps_ok=true'",
            "elif python3 -c \"import fastapi, uvicorn\" >/dev/null 2>&1; then",
            "  echo 'system_python_deps_ok=true'",
            "else",
            "  if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi",
            "  .venv/bin/python -m pip install -r jetson/requirements.txt",
            "  .venv/bin/python -c \"import fastapi, uvicorn; print('competition_venv_deps_ok=true')\"",
            "fi",
        ]
    )


def build_benchmark_command(*, remote_dir: str, iterations: int, python_candidates: tuple[str, ...]) -> str:
    validate_remote_dir(remote_dir)
    validate_python_candidates(python_candidates)
    candidates = " ".join(quote(candidate) for candidate in python_candidates)
    return "\n".join(
        [
            "set -euo pipefail",
            f"cd {quote(remote_dir)}",
            "PYTHON_BIN=''",
            f"for candidate in {candidates}; do",
            "  CANDIDATE_BIN=''",
            "  if command -v \"$candidate\" >/dev/null 2>&1; then CANDIDATE_BIN=\"$candidate\"; fi",
            "  if [ -z \"$CANDIDATE_BIN\" ] && [ -x \"$candidate\" ]; then CANDIDATE_BIN=\"$candidate\"; fi",
            "  if [ -z \"$CANDIDATE_BIN\" ]; then continue; fi",
            "  if \"$CANDIDATE_BIN\" -c \"import fastapi, uvicorn\" >/dev/null 2>&1; then PYTHON_BIN=\"$CANDIDATE_BIN\"; break; fi",
            "done",
            "if [ -z \"$PYTHON_BIN\" ]; then echo 'No usable Python found' >&2; exit 4; fi",
            "echo \"PYTHON_BIN=$PYTHON_BIN\"",
            "\"$PYTHON_BIN\" -c \"import fastapi, uvicorn; print('gateway_deps_ok=true')\"",
            f"mkdir -p {quote(REMOTE_EVIDENCE_DIR)}",
            f"rm -f {quote(REMOTE_EVIDENCE_DIR + '/08-tegrastats-http-resource-benchmark.log')}",
            "TEGRA_PID=''",
            "if command -v tegrastats >/dev/null 2>&1; then",
            f"  tegrastats --interval 1000 > {quote(REMOTE_EVIDENCE_DIR + '/08-tegrastats-http-resource-benchmark.log')} 2>&1 &",
            "  TEGRA_PID=$!",
            "fi",
            "set +e",
            (
                "WEAREDGE_AUTH_DISABLED=1 "
                "WEAREDGE_DEPLOYMENT_MODE=jetson_edge_http_gateway_benchmark "
                "WEAREDGE_EDGE_NODE_ID=jetson-orin-nano-8gb "
                "\"$PYTHON_BIN\" scripts/collect_edge_runtime_evidence.py "
                f"--rerun-benchmark --iterations {iterations} --final-edge-node --json"
            ),
            "STATUS=$?",
            "if [ -n \"$TEGRA_PID\" ]; then sleep 2; kill \"$TEGRA_PID\" >/dev/null 2>&1 || true; wait \"$TEGRA_PID\" >/dev/null 2>&1 || true; fi",
            "set -e",
            "exit $STATUS",
        ]
    )


def upload_archive(client: Any, *, local_archive: Path, remote_archive: str) -> None:
    sftp = client.open_sftp()
    try:
        remote_mkdir_p(sftp, posixpath.dirname(remote_archive))
        sftp.put(str(local_archive), remote_archive)
    finally:
        sftp.close()


def download_evidence(client: Any, *, remote_dir: str, output_dir: Path) -> list[dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sftp = client.open_sftp()
    downloaded: list[dict[str, str]] = []
    try:
        for name in REMOTE_FILES:
            remote_path = posixpath.join(remote_dir, REMOTE_EVIDENCE_DIR, name)
            local_path = output_dir / name
            try:
                sftp.stat(remote_path)
            except OSError:
                continue
            sftp.get(remote_path, str(local_path))
            downloaded.append({"name": name, "local_path": str(local_path), "remote_path": remote_path})
    finally:
        sftp.close()
    return downloaded


def copy_public_evidence(
    *,
    output_dir: Path,
    public_report: Path | None,
    public_json: Path | None,
    collection_context: dict[str, Any],
) -> dict[str, str]:
    copied: dict[str, str] = {}
    report = output_dir / "06-http-resource-benchmark-report.md"
    data = output_dir / "06-http-resource-benchmark.json"
    if public_report is not None and report.is_file():
        public_report.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(report, public_report)
        annotate_public_report(public_report, collection_context)
        copied["report"] = str(public_report)
    if public_json is not None and data.is_file():
        public_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(data, public_json)
        annotate_public_json(public_json, collection_context)
        copied["json"] = str(public_json)
    return copied


def annotate_public_report(path: Path, collection_context: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8")
    marker = "## Collection Context"
    if marker in text:
        return
    block = "\n".join(
        [
            marker,
            "",
            f"- Workstation collected at: {collection_context['workstation_collected_at_utc']}",
            f"- SSH host: `{collection_context['host']}`",
            f"- Remote competition directory: `{collection_context['remote_dir']}`",
            "- Timestamp note: benchmark `generated_at` and `tegrastats` timestamps come from the Jetson system clock.",
            "",
        ]
    )
    insertion = "\n## Boundary\n"
    if insertion in text:
        text = text.replace(insertion, f"\n{block}\n## Boundary\n", 1)
    else:
        text = f"{text.rstrip()}\n\n{block}\n"
    path.write_text(text, encoding="utf-8")


def annotate_public_json(path: Path, collection_context: dict[str, Any]) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data["collection_context"] = collection_context
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_jetson_edge_evidence(
    *,
    host: str,
    user: str,
    secret_env: str,
    remote_dir: str,
    remote_archive: str,
    output_dir: Path,
    public_report: Path | None,
    public_json: Path | None,
    iterations: int,
    timeout: float,
    skip_deploy: bool,
) -> dict[str, Any]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    validate_remote_dir(remote_dir)
    collected_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    client = connect_ssh(host=host, user=user, secret_env=secret_env, timeout=timeout)
    archive_meta: dict[str, Any] | None = None
    remote_stdout = ""
    try:
        if not skip_deploy:
            with tempfile.TemporaryDirectory(prefix="wearedge-jetson-") as tmp:
                local_archive = Path(tmp) / "wearedge-industrial-ai-agent.tar.gz"
                archive_meta = build_archive(local_archive)
                upload_archive(client, local_archive=local_archive, remote_archive=remote_archive)
            extract = exec_checked(
                client,
                build_extract_command(remote_archive=remote_archive, remote_dir=remote_dir),
                timeout=timeout,
            )
            remote_stdout += extract.stdout

        runtime = exec_checked(
            client,
            build_prepare_runtime_command(remote_dir=remote_dir),
            timeout=max(timeout, 300.0),
        )
        remote_stdout += runtime.stdout
        benchmark = exec_checked(
            client,
            build_benchmark_command(
                remote_dir=remote_dir,
                iterations=iterations,
                python_candidates=python_candidates_for_remote_dir(remote_dir),
            ),
            timeout=max(timeout, 180.0),
        )
        remote_stdout += benchmark.stdout
        downloaded = download_evidence(client, remote_dir=remote_dir, output_dir=output_dir)
        collection_context = {
            "workstation_collected_at_utc": collected_at,
            "host": host,
            "remote_dir": remote_dir,
            "timestamp_note": "Benchmark generated_at and tegrastats timestamps come from the Jetson system clock.",
        }
        public_copied = copy_public_evidence(
            output_dir=output_dir,
            public_report=public_report,
            public_json=public_json,
            collection_context=collection_context,
        )
    finally:
        client.close()

    summary = {
        "ok": any(item["name"] == "06-http-resource-benchmark.json" for item in downloaded),
        "generated_at": collected_at,
        "host": host,
        "user": user,
        "remote_dir": remote_dir,
        "output_dir": str(output_dir),
        "iterations": iterations,
        "archive": archive_meta,
        "downloaded": downloaded,
        "public_evidence": public_copied,
        "remote_stdout_tail": remote_stdout[-3000:],
    }
    summary_path = output_dir / "09-jetson-edge-evidence-collection-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deploy and collect Jetson edge-runtime evidence over SSH.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--secret-env", default="JETSON_SSH_PASSWORD")
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument("--remote-archive", default=DEFAULT_REMOTE_ARCHIVE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--public-report", type=Path, default=DEFAULT_PUBLIC_REPORT)
    parser.add_argument("--public-json", type=Path, default=DEFAULT_PUBLIC_JSON)
    parser.add_argument("--no-public-copy", action="store_true")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--skip-deploy", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    public_report = None if args.no_public_copy else args.public_report
    public_json = None if args.no_public_copy else args.public_json
    try:
        summary = collect_jetson_edge_evidence(
            host=args.host,
            user=args.user,
            secret_env=args.secret_env,
            remote_dir=args.remote_dir,
            remote_archive=args.remote_archive,
            output_dir=args.output_dir,
            public_report=public_report,
            public_json=public_json,
            iterations=args.iterations,
            timeout=args.timeout,
            skip_deploy=args.skip_deploy,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"ok={summary['ok']}")
        print(f"host={summary['host']}")
        print(f"remote_dir={summary['remote_dir']}")
        print(f"downloaded={len(summary['downloaded'])}")
        print(f"summary_path={summary['summary_path']}")
        for kind, path in summary["public_evidence"].items():
            print(f"public_{kind}={path}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
