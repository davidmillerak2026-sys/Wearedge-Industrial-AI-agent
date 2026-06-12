from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_final_external_assets.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_final_external_assets", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_external_assets_report_missing_items_without_values(tmp_path: Path) -> None:
    module = _load_module()

    result = module.verify_final_external_assets(tmp_path)
    report = module.render_report(result)

    assert result["ready"] is False
    assert result["failure_count"] >= 6
    assert "legal/company-info-filled.md" in report
    assert "does not echo company/contact values" in report


def test_final_external_assets_detects_fallback_marker(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "gongyi-mofang" / "05-run-log-ok-true.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(_fake_png())
    path.with_suffix(".fallback.json").write_text('{"provenance":"fallback"}', encoding="utf-8")

    result = module.verify_final_external_assets(tmp_path, require_video=False)

    assert any(
        failure["path"] == "gongyi-mofang/05-run-log-ok-true.png"
        and failure["code"] == "fallback_marker_present"
        for failure in result["failures"]
    )


def test_final_external_assets_can_pass_with_valid_ignored_files(tmp_path: Path) -> None:
    module = _load_module()
    _write_valid_human_files(tmp_path)
    for spec in module.WFC_LIVE_REPLACEMENTS:
        path = tmp_path / spec.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_fake_png())
    video = tmp_path / "video" / "wearedge-enterprise-demo-3-5min.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(_fake_mp4())
    (tmp_path / "video" / "wearedge-enterprise-demo-script-final.md").write_text(
        "# Final Demo Script\n\n" + "Industrial-agent narration. " * 20,
        encoding="utf-8",
    )

    result = module.verify_final_external_assets(tmp_path)

    assert result["ready"] is True
    assert result["failure_count"] == 0


def test_final_external_assets_rejects_unfilled_markdown_template(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "legal" / "company-info-filled.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Company And Contact Information\n\n"
        "| Field | Final value |\n"
        "| --- | --- |\n"
        "| Enterprise name |  |\n"
        "| Unified social credit code | TBD |\n",
        encoding="utf-8",
    )

    result = module.verify_final_external_assets(tmp_path, require_wfc_live=False, require_video=False)

    assert any(failure["code"] == "placeholder_text" for failure in result["failures"])
    assert any(failure["code"].startswith("missing_field:Enterprise name") for failure in result["failures"])


def _write_valid_human_files(root: Path) -> None:
    legal = root / "legal"
    legal.mkdir(parents=True, exist_ok=True)
    (legal / "company-info-filled.md").write_text(
        """# Company And Contact Information

## Enterprise

| Field | Final value |
| --- | --- |
| Enterprise name | Example Manufacturing Co., Ltd. |
| Unified social credit code | 914400000000000000 |
| Registered address | Example Industrial Park |
| Enterprise type | SME |
| SME eligibility confirmed | Yes |
| No adverse record confirmed | Yes |

## Project Contact

| Field | Final value |
| --- | --- |
| Project owner | Example Owner |
| Mobile | 10000000000 |
| Email | owner@example.com |
| Backup contact | Example Backup |
| Backup mobile | 10000000001 |
| Backup email | backup@example.com |

## Team Roles

| Role | Name | Responsibility | Confirmed |
| --- | --- | --- | --- |
| Project lead | Person A | Registration, business, defense coordination | Yes |
| Technical lead | Person B | Agent architecture, API, evaluation metrics | Yes |
| IT/OT integration lead | Person C | Xcelerator, Gongyi Mofang, MES/QMS/EMS/CMMS | Yes |
| Edge deployment lead | Person D | Jetson / IPC / local industrial PC evidence | Yes |
| Business lead | Person E | Target customers, business model, ROI | Yes |
| Delivery lead | Person F | Joint PoC, customer pilot, project plan | Yes |
""",
        encoding="utf-8",
    )
    (legal / "submission-contact-confirmation.md").write_text(
        """# Submission Contact Confirmation

| Field | Final value |
| --- | --- |
| Primary contact name | Example Owner |
| Primary contact mobile | 10000000000 |
| Primary contact email | owner@example.com |
| Backup contact name | Example Backup |
| Backup contact mobile | 10000000001 |
| Backup contact email | backup@example.com |
| Xcelerator account owner confirmed | Yes |
| Gongyi Mofang account owner confirmed | Yes |
| Final submitter confirmed | Yes |
""",
        encoding="utf-8",
    )
    (legal / "ip-and-no-dispute-signed.pdf").write_bytes(_fake_pdf())
    (legal / "no-adverse-record-signed.pdf").write_bytes(_fake_pdf())
    submission = root / "submission"
    submission.mkdir(parents=True, exist_ok=True)
    (submission / "01-registration-form-filled.png").write_bytes(_fake_png())
    (submission / "02-submission-success.png").write_bytes(_fake_png())


def _fake_pdf() -> bytes:
    return b"%PDF-1.7\n" + (b"0" * 1024)


def _fake_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + (b"0" * 1024)


def _fake_mp4() -> bytes:
    return b"\x00\x00\x00\x18ftypmp42" + (b"0" * 12_000)
