# Final Upload Manifest

Updated: 2026-06-12T10:01:40+00:00

## Gate

- Repository ready: True
- Live evidence ready: False
- External asset quality ready: False
- Official submission ready: False
- Bundle present: True
- Bundle SHA256: `d282538e1c7f9bdc21ba1a36aa0e105027433c8825e78d7e49c5e211fe3a1733`
- Bundle file count: `79`
- WFC resource package present: True

## Upload Queue

| Priority | Status | Attachment | Source | Audience | Action |
| --- | --- | --- | --- | --- | --- |
| P0 | ready | Business plan | `docs/submission/business-plan.md` | Official submission attachment | Convert to PDF/DOCX if the registration system requires a document format. |
| P0 | ready | Technical solution | `docs/submission/technical-solution.md` | Official submission attachment | Convert to PDF/DOCX if the registration system requires a document format. |
| P0 | ready | Repo-controlled submission bundle | `submission-assets/live-evidence/submission-bundle/wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip` | Official submission attachment or internal archive | Upload when attachment size allows; it excludes private live evidence by design. |
| P0 | ready | Final enterprise demo video | `submission-assets/live-evidence/video/wearedge-enterprise-demo-3-5min.mp4` | Official submission attachment | Use the generated 3-5 minute version; keep fallback boundaries visible. |
| P0 | ready | Registration field copy source | `docs/submission/registration-fields.md` | Copy/paste into registration system | Use short/mid/long variants; fill only real enterprise/contact values manually. |
| P1 | ready | Offline evaluation report | `docs/competition-offline-eval-report.md` | Supporting attachment | Use as proof of offline dataset validation and initial-round metric coverage. |
| P1 | ready | Final-round validation report | `docs/finals-validation-report.md` | Supporting attachment | Use as foundation evidence for multi-direction decision accuracy and coverage. |
| P1 | ready | Jetson edge HTTP latency report | `docs/finals-jetson-gateway-latency-benchmark-report.md` | Supporting attachment | Use with boundary wording: stdlib HTTP gateway fallback evidence on edge hardware. |
| P1 | ready | Xcelerator OpenAPI import spec | `openapi/wearedge-xcelerator-apiworld.openapi.json` | Technical appendix | Attach if the platform reviewer wants to reproduce API World import. |
| P1 | ready | Gongyi Mofang WFC resource package | `submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/wearedge-agent-service-0.1.0.zip` | Technical appendix | Attach as reusable component prototype; do not describe it as live WFC run proof. |
| P1 | ready | Xcelerator screenshot pack | `submission-assets/live-evidence/xcelerator/` | Supporting evidence | Use reviewed screenshots; avoid AppID/AppSecret and private contact details. |
| P1 | fallback | Gongyi Mofang screenshot pack | `submission-assets/live-evidence/gongyi-mofang/` | Supporting evidence | Replace WFC 04/05/06 fallback assets before claiming live WFC closure. |
| P2 | blocked | Signed IP/no-dispute statement | `submission-assets/live-evidence/legal/ip-and-no-dispute-signed.pdf` | Official submission attachment when required | Upload only to the official registration system or approved internal archive. |
| P2 | blocked | Signed no-adverse-record statement | `submission-assets/live-evidence/legal/no-adverse-record-signed.pdf` | Official submission attachment when required | Upload only to the official registration system or approved internal archive. |

## Blocking Items

- `legal/company-info-filled.md`: missing final live-evidence file
- `legal/ip-and-no-dispute-signed.pdf`: missing final live-evidence file
- `legal/no-adverse-record-signed.pdf`: missing final live-evidence file
- `legal/submission-contact-confirmation.md`: missing final live-evidence file
- `submission/01-registration-form-filled.png`: missing final live-evidence file
- `submission/02-submission-success.png`: missing final live-evidence file
- `gongyi-mofang/04-dashboard-decision-view.png`: fallback marker still present
- `gongyi-mofang/05-run-log-ok-true.png`: fallback marker still present
- `gongyi-mofang/06-human-approval-gate.png`: fallback marker still present
- `legal/company-info-filled.md`: quality failure: missing_or_empty
- `legal/ip-and-no-dispute-signed.pdf`: quality failure: missing_or_empty
- `legal/no-adverse-record-signed.pdf`: quality failure: missing_or_empty
- `legal/submission-contact-confirmation.md`: quality failure: missing_or_empty
- `submission/01-registration-form-filled.png`: quality failure: missing_or_empty
- `submission/02-submission-success.png`: quality failure: missing_or_empty
- `gongyi-mofang/04-dashboard-decision-view.png`: quality failure: fallback_marker_present
- `gongyi-mofang/05-run-log-ok-true.png`: quality failure: fallback_marker_present
- `gongyi-mofang/06-human-approval-gate.png`: quality failure: fallback_marker_present

## Privacy Boundary

- This manifest lists paths and statuses only; it does not include enterprise identifiers or contact values.
- Do not commit files under submission-assets/live-evidence/.
- Upload signed legal files and registration screenshots only to the official registration system or approved private archive.

## Final Checks

```powershell
python scripts/run_final_readiness_pipeline.py --json
python scripts/verify_live_evidence.py --stage final --write-manifest
python scripts/verify_final_external_assets.py --write-report
python scripts/generate_final_upload_manifest.py --write
```
