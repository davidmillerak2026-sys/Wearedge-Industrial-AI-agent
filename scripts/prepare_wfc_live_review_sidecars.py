from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from promote_wfc_live_evidence import (
    DEFAULT_SOURCE_DIR,
    TARGETS,
    WfcLiveEvidenceTarget,
    assert_png,
    review_sidecar_path,
    validate_review_sidecar,
)


TARGET_ALIASES: dict[str, str] = {
    "04": "04-dashboard-decision-view.png",
    "dashboard": "04-dashboard-decision-view.png",
    "dashboard-decision-view": "04-dashboard-decision-view.png",
    "05": "05-run-log-ok-true.png",
    "run-log": "05-run-log-ok-true.png",
    "run-log-ok-true": "05-run-log-ok-true.png",
    "06": "06-human-approval-gate.png",
    "approval": "06-human-approval-gate.png",
    "human-approval": "06-human-approval-gate.png",
    "human-approval-gate": "06-human-approval-gate.png",
}

DEFAULT_SIGNALS: dict[str, list[str]] = {
    "04-dashboard-decision-view.png": [
        "metric_cards",
        "decision_path",
        "approval_items",
        "workflow_state",
    ],
    "05-run-log-ok-true.png": [
        "ok=true",
        "wearedge_decision_ok",
        "latency",
        "function_block_output",
    ],
    "06-human-approval-gate.png": [
        "human_confirmation",
        "approval_status",
    ],
}


def _targets_by_name() -> dict[str, WfcLiveEvidenceTarget]:
    return {target.target_name: target for target in TARGETS}


def resolve_targets(values: list[str], *, all_targets: bool = False) -> list[WfcLiveEvidenceTarget]:
    targets = _targets_by_name()
    if all_targets:
        return list(TARGETS)
    if not values:
        raise ValueError("select at least one --target or pass --all-targets")

    resolved: list[WfcLiveEvidenceTarget] = []
    seen: set[str] = set()
    for raw in values:
        key = raw.strip().lower()
        name = TARGET_ALIASES.get(key, raw.strip())
        if name not in targets:
            allowed = ", ".join(sorted(set(TARGET_ALIASES) | set(targets)))
            raise ValueError(f"unknown WFC target {raw!r}; allowed values: {allowed}")
        if name not in seen:
            resolved.append(targets[name])
            seen.add(name)
    return resolved


def build_review_payload(
    target: WfcLiveEvidenceTarget,
    *,
    source_url: str,
    captured_at_utc: str,
    reviewer_role: str,
    operator_note: str,
    extra_signals: list[str],
    template_only: bool = False,
) -> dict[str, Any]:
    observed = list(DEFAULT_SIGNALS[target.target_name])
    for signal in extra_signals:
        normalized = signal.strip()
        if normalized and normalized not in observed:
            observed.append(normalized)

    payload: dict[str, Any] = {
        "live_wfc_source": not template_only,
        "source_url": source_url,
        "captured_at_utc": captured_at_utc,
        "reviewer_role": reviewer_role,
        "observed_signals": observed,
        "operator_note": operator_note,
        "target": target.target_name,
        "acceptance": target.acceptance,
    }
    return payload


def prepare_review_sidecars(
    *,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    selected_targets: list[WfcLiveEvidenceTarget],
    source_url: str,
    captured_at_utc: str | None = None,
    reviewer_role: str = "WFC operator",
    operator_note: str = "",
    extra_signals: list[str] | None = None,
    template_only: bool = False,
) -> dict[str, Any]:
    source_dir = source_dir.resolve()
    source_dir.mkdir(parents=True, exist_ok=True)
    timestamp = captured_at_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    signals = extra_signals or []

    prepared: list[dict[str, Any]] = []
    for target in selected_targets:
        screenshot = source_dir / target.target_name
        if template_only:
            review_path = source_dir / target.target_name.replace(".png", ".review.template.json")
        else:
            if not screenshot.is_file():
                raise FileNotFoundError(
                    f"missing live WFC screenshot: {screenshot}. "
                    "Capture the PNG first, or use --template-only to write non-promotable templates."
                )
            assert_png(screenshot)
            review_path = review_sidecar_path(screenshot)

        payload = build_review_payload(
            target,
            source_url=source_url,
            captured_at_utc=timestamp,
            reviewer_role=reviewer_role,
            operator_note=operator_note,
            extra_signals=signals,
            template_only=template_only,
        )
        if not template_only:
            validate_review_sidecar(payload, target=target, path=review_path)

        review_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        prepared.append(
            {
                "target": target.target_name,
                "screenshot": str(screenshot),
                "review_sidecar": str(review_path),
                "template_only": template_only,
                "observed_signals": payload["observed_signals"],
            }
        )

    return {
        "ok": True,
        "source_dir": str(source_dir),
        "template_only": template_only,
        "prepared_count": len(prepared),
        "prepared": prepared,
        "next_step": (
            "Capture real WFC PNG screenshots, then rerun without --template-only."
            if template_only
            else "Run scripts/promote_wfc_live_evidence.py with --require-review-sidecars after visual review."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare reviewed WFC live evidence sidecars for promotion."
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--all-targets", action="store_true")
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--captured-at-utc")
    parser.add_argument("--reviewer-role", default="WFC operator")
    parser.add_argument("--operator-note", default="")
    parser.add_argument("--observed-signal", action="append", default=[])
    parser.add_argument("--template-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        selected = resolve_targets(args.target, all_targets=args.all_targets)
        result = prepare_review_sidecars(
            source_dir=args.source_dir,
            selected_targets=selected,
            source_url=args.source_url,
            captured_at_utc=args.captured_at_utc,
            reviewer_role=args.reviewer_role,
            operator_note=args.operator_note,
            extra_signals=args.observed_signal,
            template_only=args.template_only,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result['ok']}")
        print(f"prepared={result['prepared_count']}")
        for item in result["prepared"]:
            print(f"{item['target']} -> {item['review_sidecar']}")
        print(result["next_step"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
