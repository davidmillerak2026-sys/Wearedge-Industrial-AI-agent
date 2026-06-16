from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FUNCTION_BLOCK = REPO_ROOT / "workflows" / "wfc_call_wearedge_decision_fb_main.py"
DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "submission-assets"
    / "live-evidence"
    / "gongyi-mofang"
    / "wfc-live-edit-package"
)


def build_package(
    *,
    function_block: Path = DEFAULT_FUNCTION_BLOCK,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    function_block = _resolve(function_block)
    output_dir = _resolve(output_dir)
    source = function_block.read_text(encoding="utf-8")
    if "wfc_writeback" not in source:
        raise ValueError("function block source must include wfc_writeback status")

    output_dir.mkdir(parents=True, exist_ok=True)
    fb_target = output_dir / "fb_main.py"
    shutil.copyfile(function_block, fb_target)

    sample_resource = {
        "agentHost": "http://<edge-or-stable-host>",
        "agentPort": 8081,
        "deploymentMode": "edge-fastapi-gateway",
        "plantId": "demo-plant-a",
        "lineId": "line-bearing-01",
        "apiKeyRef": "",
        "note": "Do not put secrets in this file. Use WFC secret/reference fields if required.",
    }
    (output_dir / "wfc-resource-input-sample.json").write_text(
        json.dumps(sample_resource, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    checklist = render_checklist(function_block, fb_target)
    (output_dir / "README-next-live-run.md").write_text(checklist, encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": str(function_block),
        "output_dir": str(output_dir),
        "files": {
            "function_block": str(fb_target),
            "sample_resource": str(output_dir / "wfc-resource-input-sample.json"),
            "checklist": str(output_dir / "README-next-live-run.md"),
        },
        "function_block_chars": len(source),
        "function_block_lines": source.count("\n") + 1,
        "acceptance": [
            "CallWearedgeDecisionApi.output shows ok=true.",
            "CallWearedgeDecisionApi.output includes wfc_writeback.method=wfc_output1_to_update_data_table.",
            "Preferred: WFC has a visible output1-to-UpdateDataTable data-port connection.",
            "Final proof: the native data table shows fields_ready values after the run.",
        ],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def render_checklist(function_block: Path, fb_target: Path) -> str:
    return "\n".join(
        [
            "# WFC Live Edit Package",
            "",
            "Purpose: paste the updated `fb_main.py` into the Gongyi Mofang Python Function Block, run DEBUG, and capture stronger live evidence for output1-to-UpdateDataTable writeback.",
            "",
            "## Files",
            "",
            f"- Source function block: `{function_block}`",
            f"- Paste-ready function block: `{fb_target}`",
            "- Resource input sample: `wfc-resource-input-sample.json`",
            "",
            "## Live WFC Steps",
            "",
            "1. Open the live `Wearedge WFC PoC` project.",
            "2. Open the `CallWearedgeDecisionApi` Python Function Block.",
            "3. Replace `fb_main.py` with the paste-ready file in this package.",
            "4. Set the resource/input block to the current edge or stable endpoint.",
            "5. Run DEBUG.",
            "6. Capture the native output/log screenshot if `output1` includes `ok=true` and `wfc_writeback`.",
            "7. Confirm the `output1` data port is connected to `UpdateDataTable` input.",
            "8. Open the native data table and capture values after the run if fields changed dynamically.",
            "",
            "## Screenshot Targets",
            "",
            "- `submission-assets/live-evidence/gongyi-mofang/196-wfc-dynamic-writeback-output-ok-20260616.png`",
            "- `submission-assets/live-evidence/gongyi-mofang/197-wfc-data-table-values-after-python-writeback-20260616.png`",
            "- Optional: `submission-assets/live-evidence/gongyi-mofang/198-wfc-output1-to-update-table-data-wire-20260616.png`",
            "",
            "## Acceptance",
            "",
            "- Minimum: `CallWearedgeDecisionApi.output` shows `ok=true` and `wfc_writeback.method=wfc_output1_to_update_data_table`.",
            "- Best: a native WFC data-line screenshot showing `output1 -> UpdateDataTable` input.",
            "- Final proof: native WFC data-table values match `wfc_writeback.fields_ready` after the run.",
            "- Do not commit screenshots or secrets from `submission-assets/live-evidence/`.",
            "",
        ]
    )


def _resolve(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a paste-ready WFC Function Block live edit package.")
    parser.add_argument("--function-block", type=Path, default=DEFAULT_FUNCTION_BLOCK)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    manifest = build_package(function_block=args.function_block, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"output_dir={manifest['output_dir']}")
        print(f"function_block={manifest['files']['function_block']}")
        print(f"checklist={manifest['files']['checklist']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
