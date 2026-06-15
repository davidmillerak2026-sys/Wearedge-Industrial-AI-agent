from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSETS_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "gongyi-mofang"
DEFAULT_SOURCE_DIR = REPO_ROOT / "submission-assets" / "live-evidence" / "gongyi-mofang-live-source"
MANIFEST_NAME = "wfc-live-evidence-replacement-manifest.json"


@dataclass(frozen=True)
class WfcLiveEvidenceTarget:
    target_name: str
    title: str
    acceptance: str
    source_aliases: tuple[str, ...]
    fallback_sidecars: tuple[str, ...] = (".fallback.json",)
    review_signals: tuple[str, ...] = ()
    review_signal_mode: str = "any"


TARGETS: tuple[WfcLiveEvidenceTarget, ...] = (
    WfcLiveEvidenceTarget(
        target_name="04-dashboard-decision-view.png",
        title="Workflow Canvas dashboard decision view",
        acceptance="Live WFC Dashboard/ui-builder view showing metric cards, decision path, approval items, and workflow state.",
        source_aliases=("04-dashboard-decision-view.png", "dashboard-decision-view.png", "dashboard.png"),
        review_signals=("metric_cards", "decision_path", "approval_items", "workflow_state"),
        review_signal_mode="all",
    ),
    WfcLiveEvidenceTarget(
        target_name="05-run-log-ok-true.png",
        title="Workflow Canvas run log ok=true",
        acceptance="Live WFC log-manager or run output showing ok=true, wearedge_decision_ok, latency, function blocks, or table writeback.",
        source_aliases=("05-run-log-ok-true.png", "run-log-ok-true.png", "run-log.png"),
        fallback_sidecars=(".fallback.json", ".fallback.html"),
        review_signals=("ok=true", "wearedge_decision_ok", "latency", "function_block_output", "table_writeback"),
    ),
    WfcLiveEvidenceTarget(
        target_name="06-human-approval-gate.png",
        title="HumanApprovalGate live view",
        acceptance="Live WFC human confirmation node, approval panel, or Dashboard approval item for high-risk OT actions.",
        source_aliases=("06-human-approval-gate.png", "human-approval-gate.png", "approval-gate.png"),
        review_signals=("pending", "approved", "rejected", "human_confirmation", "approval_status"),
    ),
)

ALLOWED_WFC_SOURCE_PREFIXES = (
    "https://wfc.bd-iiot.com/",
    "https://sitescope.wfc.bd-iiot.com/",
    "https://spidr.wfc.bd-iiot.com/",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_png(path: Path) -> None:
    with path.open("rb") as handle:
        header = handle.read(8)
    if header != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"source screenshot must be a PNG file: {path}")


def find_source(source_dir: Path, target: WfcLiveEvidenceTarget) -> Path:
    for name in target.source_aliases:
        candidate = source_dir / name
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    aliases = ", ".join(target.source_aliases)
    raise FileNotFoundError(f"missing live source screenshot for {target.target_name}; expected one of: {aliases}")


def review_sidecar_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}.review.json")


def load_review_sidecar(source: Path, target: WfcLiveEvidenceTarget) -> dict[str, Any]:
    path = review_sidecar_path(source)
    if not path.is_file():
        raise FileNotFoundError(
            f"missing review sidecar for {source.name}; expected {path.name}. "
            "Create it only after reviewing the live WFC screenshot."
        )
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid review sidecar JSON: {path}") from exc
    if not isinstance(review, dict):
        raise ValueError(f"review sidecar must be a JSON object: {path}")
    validate_review_sidecar(review, target=target, path=path)
    return review


def validate_review_sidecar(review: dict[str, Any], *, target: WfcLiveEvidenceTarget, path: Path) -> None:
    if review.get("live_wfc_source") is not True:
        raise ValueError(f"{path.name} must set live_wfc_source=true")

    source_url = str(review.get("source_url", "")).strip()
    if not source_url.startswith(ALLOWED_WFC_SOURCE_PREFIXES):
        allowed = ", ".join(ALLOWED_WFC_SOURCE_PREFIXES)
        raise ValueError(f"{path.name} source_url must start with one of: {allowed}")

    captured_at = str(review.get("captured_at_utc", "")).strip()
    if "T" not in captured_at or not captured_at.endswith(("Z", "+00:00")):
        raise ValueError(f"{path.name} must include captured_at_utc in UTC ISO-like format")

    signals_value = review.get("observed_signals", [])
    if not isinstance(signals_value, list) or not all(isinstance(item, str) for item in signals_value):
        raise ValueError(f"{path.name} observed_signals must be a list of strings")
    signals = {item.strip().lower() for item in signals_value if item.strip()}
    required = {item.lower() for item in target.review_signals}
    if target.review_signal_mode == "all":
        missing = sorted(required - signals)
        if missing:
            raise ValueError(f"{path.name} is missing required observed_signals: {', '.join(missing)}")
    elif required and not (required & signals):
        raise ValueError(
            f"{path.name} must include at least one observed_signal from: {', '.join(sorted(required))}"
        )
    elif target.review_signal_mode != "any":
        raise ValueError(f"unknown review_signal_mode for {target.target_name}: {target.review_signal_mode}")


def summarize_review(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_url": str(review.get("source_url", "")).strip(),
        "captured_at_utc": str(review.get("captured_at_utc", "")).strip(),
        "reviewer_role": str(review.get("reviewer_role", "")).strip(),
        "observed_signals": review.get("observed_signals", []),
    }


def resolve_inside_workspace(path: Path) -> Path:
    resolved = path.resolve()
    workspace = REPO_ROOT.resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"path must stay inside the repository workspace: {path}") from exc
    return resolved


def promote_wfc_live_evidence(
    *,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    assets_dir: Path = DEFAULT_ASSETS_DIR,
    confirm_live_source: bool,
    operator_note: str = "",
    require_review_sidecars: bool = False,
) -> dict[str, Any]:
    if not confirm_live_source:
        raise ValueError("refusing to promote WFC evidence without --confirm-live-source")

    source_dir = resolve_inside_workspace(source_dir)
    assets_dir = resolve_inside_workspace(assets_dir)
    if source_dir == assets_dir:
        raise ValueError("source_dir must be a staging folder, not the active Gongyi Mofang evidence folder")

    promoted_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    assets_dir.mkdir(parents=True, exist_ok=True)
    promoted: list[dict[str, Any]] = []
    removed_sidecars: list[str] = []

    for target in TARGETS:
        source = find_source(source_dir, target)
        assert_png(source)
        review = load_review_sidecar(source, target) if require_review_sidecars else None
        destination = assets_dir / target.target_name
        if source.resolve() == destination.resolve():
            raise ValueError(f"source and destination must be different files: {source}")

        shutil.copyfile(source, destination)
        sidecars_removed_for_target: list[str] = []
        for suffix in target.fallback_sidecars:
            sidecar = assets_dir / target.target_name.replace(".png", suffix)
            if sidecar.exists():
                sidecar.unlink()
                sidecars_removed_for_target.append(sidecar.name)
                removed_sidecars.append(sidecar.name)

        promoted.append(
            {
                "target": target.target_name,
                "title": target.title,
                "acceptance": target.acceptance,
                "source": str(source.relative_to(REPO_ROOT)),
                "destination": str(destination.relative_to(REPO_ROOT)),
                "bytes": destination.stat().st_size,
                "sha256": sha256_file(destination),
                "removed_fallback_sidecars": sidecars_removed_for_target,
                "review": summarize_review(review) if review else None,
            }
        )

    manifest = {
        "ok": True,
        "promoted_at_utc": promoted_at,
        "source_dir": str(source_dir.relative_to(REPO_ROOT)),
        "assets_dir": str(assets_dir.relative_to(REPO_ROOT)),
        "operator_confirmation": "live WFC screenshots were reviewed before promotion",
        "operator_note": operator_note,
        "review_sidecars_required": require_review_sidecars,
        "promoted": promoted,
        "removed_fallback_sidecars": removed_sidecars,
        "next_check": "python scripts/verify_live_evidence.py --stage platform --write-manifest",
    }
    manifest_path = assets_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Promote reviewed live Gongyi Mofang WFC screenshots over fallback evidence."
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--assets-dir", type=Path, default=DEFAULT_ASSETS_DIR)
    parser.add_argument("--confirm-live-source", action="store_true")
    parser.add_argument("--require-review-sidecars", action="store_true")
    parser.add_argument("--operator-note", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = promote_wfc_live_evidence(
            source_dir=args.source_dir,
            assets_dir=args.assets_dir,
            confirm_live_source=args.confirm_live_source,
            operator_note=args.operator_note,
            require_review_sidecars=args.require_review_sidecars,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"ok={manifest['ok']}")
        print(f"promoted={len(manifest['promoted'])}")
        print(f"manifest={manifest['manifest_path']}")
        for item in manifest["promoted"]:
            print(f"{item['target']} <- {item['source']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
