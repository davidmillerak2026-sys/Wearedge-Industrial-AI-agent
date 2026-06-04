# WearEdge Pro Test Log History

This document consolidates the test and deployment logs that were previously spread across terminal output, Jetson runs, and project notes. Keep appending new validation records here after local tests, Jetson deployments, M400 POC runs, or field demos.

Timezone note: unless otherwise stated, human-readable times are Asia/Shanghai. Jetson API timestamps are UTC.

## Current Status

| Area | Latest Result | Notes |
| --- | --- | --- |
| Local automated tests | Passed, `122 passed` | Run on Windows project workspace with Anaconda Python. |
| Jetson gateway | Passed | `wearedge-gateway.service` active, `/healthz` OK. |
| Jetson pytest suite | Not installed | Jetson `.venv` and system Python do not have `pytest`; this does not affect runtime service. |
| Jetson lao-shi-fu POC | Passed | Full maintenance session POC passed through real gateway and llama.cpp. |
| Jetson IQC POC | Passed | Simulated M400 product-defect image plus detector evidence returned QMS `quality_hold` through real gateway. |
| Jetson 5-agent gateway sweep | Passed | maintenance, hazard, iQC, WI, and Changeover allow/block scenarios passed through real gateway or session API. |
| RAG / KB | Passed | `knowledge_base.status=matched`. |
| Maintenance threshold evaluation | Passed | `maintenance_evaluation.status=breach_detected`, `risk_level=high`, `breach_count=5`. |
| IQC quality-plan evaluation | Passed | Local quality-plan RAG, detector evidence contract, and detector-first guard added for `AL-HOUSING-L3`. |
| WI / Changeover released-source guard | Passed | Local released WI and changeover checklist retrieval block untrusted guidance when source evidence is missing. |
| Runtime trace | Passed | `runtime_stream.closed=true`, audit logged. |
| M400 real-device full chain | Passed | Vuzix M400 Camera2 JPEG upload to Jetson `maintenance` agent completed; M400 `Audit Recent` matched the same request id. |
| M400 voice adapter | Passed | WearEdge app-level command adapter triggered maintenance mode, gateway health, Camera2 capture, Jetson upload, and audit match on real M400. |
| M400 custom voice phrases | Passed | Native Vuzix custom phrases `check gateway`, `capture frame`, `maintenance mode`, and `upload to Jetson` triggered real M400 app actions and completed a Jetson maintenance inference. |
| M400 lao-shi-fu iterative session loop | Implemented, live run pending | M400 client now supports one-tap field launch, auto Jetson connection, auto session creation, evidence upload, session inference, next-evidence prompts, and trace; live repeated M400 capture loop still needs to be executed on the glasses. |
| M400 voice control | Passed | Vuzix system speech command bubbles operated WearEdge M400 app controls: voice-triggered Camera2 capture and upload-button path. |

## Key Artifact Paths

Local workspace:

```text
C:\Users\ryan hui\Documents\New project\WearEdge-Pro
C:\Users\ryan hui\Documents\New project\WearEdge-Pro\wearedge-pro-latest.tar
```

Jetson:

```text
~/WearEdge-Pro
/tmp/wearedge-pro-latest.tar
/tmp/wearedge-maintenance-session-poc/run.log
/tmp/wearedge-maintenance-session-poc/08_infer_response.json
/tmp/wearedge-maintenance-session-poc/09_trace.json
/tmp/wearedge-iqc-poc-response.json
/tmp/wearedge-iqc-detector-poc-response.json
/tmp/wearedge-full-agent-poc
```

## Log Timeline

### 2026-05-18: M400 Native Custom Voice Phrases Test

Purpose:

Validate direct WearEdge phrases through the native Vuzix speech service, without relying on numbered speech bubbles and without changing Jetson Gateway APIs.

Implementation:

```text
SDK: com.vuzix:sdk-speechrecognitionservice:1.97.1
Native action: com.vuzix.action.VOICE_COMMAND
Native extra: phrase
WearEdge adapter action: com.wearedge.m400demo.action.VOICE_COMMAND
Registered custom phrases: 12
```

Validated direct phrases:

```text
check gateway
capture frame
maintenance mode
upload to Jetson
```

Result:

```text
request_id: 2eb9f7cfa49f48f090f82cf387b13b66
analysis_mode: maintenance
capture_mode: voice-adapter-camera2
latency_ms: 45122
saved_path: /mnt/nvme/wearedge/uploads/1779098027600.jpg
channel: maintenance_identification_required
priority: medium
```

Evidence:

```text
docs/poc-results/m400-custom-voice-phrases-2026-05-18/evidence-manifest.md
docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-result-summary.json
docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-jetson-upload-1779098027600.jpg
docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-current-result-screen.png
docs/poc-results/m400-custom-voice-phrases-2026-05-18/custom-voice-current-debug-screen.png
```

### 2026-05-18: WearEdge Voice Adapter Real-M400 Test

Purpose:

Implement and validate a WearEdge-owned voice command adapter inside the M400 Android app, so voice events can trigger existing app actions without changing Jetson Gateway APIs.

Implementation:

```text
Adapter action: com.wearedge.m400demo.action.VOICE_COMMAND
Command aliases: maintenance, health, capture, upload, audit
Numeric aliases: 3=capture, 4=upload, 5=health, 6=audit
Files: clients/m400/android/app/src/main/java/com/wearedge/m400demo/WearEdgeVoiceAdapter.kt
       clients/m400/android/app/src/main/java/com/wearedge/m400demo/MainActivity.kt
```

Validation:

```text
M400 device: M005043620
Build: .\gradlew.bat :app:assembleDebug --no-daemon -> BUILD SUCCESSFUL
Install: adb install -r app-debug.apk -> Success
health command: Gateway health OK
capture command: Camera2 JPEG 1280x720 captured
upload command: Jetson maintenance inference completed
audit command: request_id_matched=true
```

Result:

```text
request_id: 68a79723fbde47f2a276cc2e9208bf4f
analysis_mode: maintenance
capture_mode: voice-adapter-camera2
latency_ms: 46778
saved_path: /mnt/nvme/wearedge/uploads/1779096333543.jpg
channel: maintenance_identification_required
priority: medium
```

Evidence:

```text
docs/poc-results/m400-voice-adapter-2026-05-18/evidence-manifest.md
docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-result-summary.json
docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-audit-match.png
docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-upload-action.png
docs/poc-results/m400-voice-adapter-2026-05-18/voice-adapter-jetson-upload-1779096333543.jpg
```

### 2026-05-18: Vuzix M400 Voice-Control Functional Check

Purpose:

Verify that the real Vuzix M400 can operate the existing WearEdge M400 demo app through system voice control, without changing the WearEdge API schema.

Setup:

```text
M400 device: Vuzix_M400 / M005043620
App package: com.wearedge.m400demo
Activity: com.wearedge.m400demo/.MainActivity
Vuzix accessibility service: com.vuzix.accessibilityservice/.AccessibilitySpeechInput
accessibility_enabled=1
```

Validation:

```text
Hello Vuzix -> Command list: passed
Hello Vuzix -> numbered speech bubbles over WearEdge controls: passed
Hello Vuzix -> three -> Capture Camera2 JPEG: passed
Hello Vuzix -> four -> Upload To Jetson button path: passed
```

Key observations:

```text
The M400 recognized "Hello Vuzix" and opened the Vuzix Speech command list.
After enabling AccessibilitySpeechInput, WearEdge controls received numbered bubbles.
Bubble 3 mapped to Capture Camera2 JPEG.
Bubble 4 mapped to Upload To Jetson.
The "three" voice command captured a Camera2 JPEG and enabled Upload To Jetson.
The "four" voice command invoked the upload button path and stopped at expected local validation because the demo token was not entered in the current app session.
```

Local evidence:

```text
docs/poc-results/m400-voice-control-2026-05-18/evidence-manifest.md
docs/poc-results/m400-voice-control-2026-05-18/m400-voice-after-tts-command-list.png
docs/poc-results/m400-voice-control-2026-05-18/m400-voice-number-bubbles-before-three.png
docs/poc-results/m400-voice-control-2026-05-18/m400-voice-after-say-three.png
docs/poc-results/m400-voice-control-2026-05-18/m400-voice-upload-bubbles-before-four.png
docs/poc-results/m400-voice-control-2026-05-18/m400-voice-after-say-four-upload-local-check.png
```

Conclusion:

Vuzix system speech control can operate the existing WearEdge M400 app controls through numbered on-screen speech bubbles. This validates the first hands-free control path for M400 field use, while keeping custom production voice phrases as a later UI/UX improvement.

Risk boundary:

This run proves system-level voice control over visible app buttons. It does not yet prove a polished custom command grammar such as "capture frame" or "upload to Jetson", nor a fully voice-only upload when secure token/config entry is absent from the current app session.

### 2026-05-18: Vuzix M400 Real-Device Full-Chain Debug

Purpose:

Run one real Vuzix M400 capture through the production Jetson gateway and confirm the result on the M400 client, without changing the existing API schema.

Setup:

```text
M400 device: Vuzix_M400 / M005043620
M400 network: same Wi-Fi as Jetson, device IP observed as 192.168.0.159
Jetson gateway: http://192.168.0.155:8081
analysis_mode: maintenance
device_id: m400-demo-01
capture_mode: camera2-manual-trigger
```

Jetson recovery before test:

```text
Issue: llama service failed because local model files were missing after workspace alignment.
Recovery: restored Gemma 4 E2B GGUF files from the Jetson worktree backup into /mnt/nvme/models/gemma4-e2b and restored the repo symlink.
Result: wearedge-llama.service active on :8080, wearedge-gateway.service active on :8081.
```

Validation:

```text
Check Gateway: passed
Camera2 preview/JPEG: passed, JPEG 1280x720
Upload To Jetson: passed
Audit Recent: passed
```

Key inference evidence:

```text
request_id=e30eb8d0a20d441dba5b0b5f849351e1
received_at=2026-05-18T04:08:27.340251Z
latency_ms=44907
saved_path=/mnt/nvme/wearedge/uploads/1779077307340.jpg
channel=maintenance_identification_required
priority=medium
owner=maintenance_engineer
runtime_events=33
runtime_last_event=workflow.closed
contract_ok=true
audit_logged=true
```

M400-visible action:

```text
Inspect the motor's external condition for signs of overheating, excessive noise, or visible fluid leaks before proceeding with any further diagnostic steps.
```

Audit match:

```text
audit.ok=true
audit.enabled=true
latest_request_id=e30eb8d0a20d441dba5b0b5f849351e1
last_inference_request_id=e30eb8d0a20d441dba5b0b5f849351e1
request_id_matched=true
```

Local evidence captured during the run:

```text
docs/poc-results/m400-real-device-full-chain-2026-05-18/evidence-manifest.md
docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-to-jetson-lao-shi-fu-process-report.md
docs/poc-results/m400-real-device-full-chain-2026-05-18/performance-summary.json
docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-captured-frame-1779077307340.jpg
docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-after-upload2.png
docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-audit-details.png
docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-audit-recent-latest.json
```

Screenshot and evidence times:

```text
2026-05-18 12:11:33 CST  m400-after-upload2.png
2026-05-18 12:13:40 CST  m400-audit-details.png
2026-05-18 12:13:59 CST  m400-audit-recent-latest.json
2026-05-18 16:17:46 CST  m400-captured-frame-1779077307340.jpg
```

Raw image snapshot:

```text
Jetson source path: /mnt/nvme/wearedge/uploads/1779077307340.jpg
Repository snapshot: docs/poc-results/m400-real-device-full-chain-2026-05-18/m400-captured-frame-1779077307340.jpg
SHA256: 1EEF797D78A7C6F7EABB4A7FA922715CF8076A7418B07BC2830E02D208BD867C
```

Conclusion:

The real-device path is validated end to end: M400 Camera2 capture -> Wi-Fi upload -> Jetson FastAPI gateway -> local llama.cpp multimodal inference -> structured maintenance action -> M400 result display -> audit lookup matching the same request id.

Product-performance report:

```text
The comprehensive process report now records the M400 operator flow, raw field image, M400 result UI, Jetson lao-shi-fu agent feedback, runtime stage trace, audit match, supported claims, and unsupported risk boundary for external review.
```

Risk boundary:

This run proves one real M400 maintenance capture loop. It does not yet prove production UI polish, voice-first operation, offline Wi-Fi provisioning, long-duration M400 battery behavior, or machine-specific maintenance recommendations. The maintenance agent correctly required human confirmation because the captured image did not include trusted machine identity or connected telemetry/manual evidence.

### 2026-05-14: Jetson Full 5-Agent Gateway Sweep

Purpose:

Run the complete WearEdge five-agent set through the real Jetson gateway after the WI/Changeover source-evaluation POC. Maintenance uses the dedicated multi-evidence session API; Hazard, IQC, WI, and Changeover use `/v1/infer`.

Local pre-check:

```text
122 passed in 1.01s
```

Gateway health:

```text
gateway_ok=true
model=gemma4
visual_tokens=560/560
```

Result:

```text
case=maintenance_session
latency_ms_gateway=79937
action_channel=maintenance_report
action_owner=maintenance_engineer
integration_target=maintenance_work_order
knowledge_base.status=matched
maintenance_evaluation.status=breach_detected
maintenance_evaluation.risk_level=high
breach_count=5
evidence_count=6
runtime_stream.closed=true
pass=true

case=hazard_exposure
latency_ms_gateway=39575
action_channel=stop_and_make_safe
action_owner=operator
integration_target=ehs_case
requires_human_action=true
runtime_stream.closed=true
pass=true

case=iqc_detector_quality_hold
latency_ms_gateway=44966
detector_evidence.status=available
quality_evaluation.status=detector_or_plan_risk_detected
quality_evaluation.recommended_channel=quality_hold
action_channel=quality_hold
integration_target=qms_quality_event
runtime_stream.closed=true
pass=true

case=wi_allow_cartoner_st2
latency_ms_gateway=84522
machine=CARTONER-ST2
source_evaluation.source_status=matched
source_evaluation.status=released_source_matched
action_channel=guided_operation
integration_target=wi_reference
runtime_stream.closed=true
pass=true

case=changeover_allow_labeler_c500
latency_ms_gateway=44032
machine=LABELER-FL1
sku=SKU-C500
source_evaluation.source_status=matched
source_evaluation.status=released_source_matched
action_channel=controlled_changeover_step
integration_target=changeover_checklist
runtime_stream.closed=true
pass=true

case=changeover_block_labeler_x999
latency_ms_gateway=44126
machine=LABELER-FL1
sku_observed_by_model=SKU-X99
source_evaluation.source_status=no_match
source_evaluation.status=missing_released_source
action_channel=changeover_source_required
integration_target=changeover_checklist
runtime_stream.closed=true
pass=true
```

Issues found and fixed:

- Jetson shell scripts had CRLF line endings, causing `/usr/bin/env: 'bash\r': No such file or directory`. Added `.gitattributes` with `*.sh text eol=lf`, converted local `scripts/*.sh` to LF, and converted Jetson scripts before rerun.
- The first Hazard run returned `502` because the old hazard prompt template said `one short phrase` while validation required more than 15 words. Hardened the hazard prompt and repair prompt to request complete industrial safety sentences; the retry passed with `stop_and_make_safe`.

Artifact paths:

- `runtime/full-agent-gateway-poc/summary.json`
- `docs/poc-results/full-agent-gateway-poc-summary.json`
- `runtime/full-agent-gateway-poc/maintenance_session_response.json`
- `runtime/full-agent-gateway-poc/hazard_exposure_retry.json`
- `runtime/full-agent-gateway-poc/iqc_detector_quality_hold.json`
- `runtime/full-agent-gateway-poc/wi_allow_cartoner_st2.json`
- `runtime/full-agent-gateway-poc/changeover_allow_labeler_c500.json`
- `runtime/full-agent-gateway-poc/changeover_block_labeler_x999.json`

### 2026-05-14: Jetson WI / Changeover Source Evaluation Gateway POC

Purpose:

Run real Jetson `/v1/infer` calls with simulated M400 images for General WI and Changeover, then verify `source_evaluation` can allow matched released sources and block unmatched changeover guidance under real VLM output.

Input images:

- `docs/assets/wi-changeover-source-poc/wi_cartoner_st2_released_wi_m400.jpg`
- `docs/assets/wi-changeover-source-poc/changeover_labeler_fl1_sku_c500_m400.jpg`
- `docs/assets/wi-changeover-source-poc/changeover_labeler_fl1_sku_x999_m400.jpg`

Gateway health:

```text
gateway_ok=true
model=gemma4
visual_tokens=560/560
```

Result:

```text
case=wi_allow_cartoner_st2
http_status=200
latency_ms_gateway=43298
machine=CARTONER-ST2
source_status=matched
source_eval_status=released_source_matched
recommended_channel=guided_operation
action_channel=guided_operation
requires_human_action=false
runtime_stream.closed=true
pass=true

case=changeover_allow_labeler_c500
http_status=200
latency_ms_gateway=44576
machine=LABELER-FL1
sku=SKU-C500
source_status=matched
source_eval_status=released_source_matched
recommended_channel=controlled_changeover_step
action_channel=controlled_changeover_step
requires_human_action=false
runtime_stream.closed=true
pass=true

case=changeover_block_labeler_x999
http_status=200
latency_ms_gateway=43766
machine=LABELER-FL1
sku_observed_by_model=SKU-X99
source_status=no_match
source_eval_status=missing_released_source
recommended_channel=changeover_source_required
action_channel=changeover_source_required
requires_human_action=true
runtime_stream.closed=true
pass=true
```

Key observations:

- WI allow path worked through the real model: the model identified `CARTONER-ST2`, fallback source retrieval matched `WI-CARTONER-ST2`, and final action remained `guided_operation`.
- Changeover allow path worked through the real model: the model identified `LABELER-FL1` and `SKU-C500`, source retrieval matched `CO-LABELER-FL1-SKU-C500`, and final action remained `controlled_changeover_step`.
- Changeover block path worked as the industrial guard: the model proposed a low-control `Set...` action, but source evidence did not match a released checklist, so `released_source_guard` changed the final channel to `changeover_source_required`.
- The model read `SKU-X999` as `SKU-X99` in the blocked image, which is acceptable for this guard test because the source evaluator still produced `source_status=no_match` and avoided a false C500 match.

Artifact paths:

- `runtime/wi-changeover-poc/*.json`
- `docs/poc-results/wi-changeover-source-eval-poc-summary.json`
- `docs/assets/wi-changeover-source-poc/`

### 2026-05-14: Jetson Deploy - Released-Source Guard Flow Check

Purpose:

Deploy the latest WearEdge-Pro package to Jetson and confirm the gateway exposes the WI/Changeover released-source stages in the real `/v1/agent-flow` response.

Result:

```text
gateway_ok=true
service_active=active
supported_modes=["changeover","hazard","iqc","maintenance","wi"]
stage_count=30
released_source_stages_present=true
missing_released_source_stages=[]
```

Confirmed stages:

- `retrieve_released_wi_source`
- `retrieve_changeover_checklist`
- `evaluate_released_source`
- `released_source_guard`

Notes:

- Deployment package: `wearedge-pro-latest.tar`
- Jetson gateway was restarted after extraction.
- This was a lightweight contract/flow check; the next live POC should run real M400-style WI and Changeover images through `/v1/infer`.

### 2026-05-14: WI / Changeover Released-Source Guard

Purpose:

Harden the third and fourth industrial agent paths after lao-shi-fu and IQC: General WI and Changeover now retrieve released source evidence before allowing trusted operation guidance or controlled changeover steps.

Command:

```powershell
& 'C:\Users\ryan hui\anaconda3\python.exe' -m pytest -q
```

Result:

```text
122 passed in 1.00s
```

Key output:

- Added `jetson/released_source.py` with released-source retrieval and deterministic source evaluation.
- Added `data/released_sources/cartoner_station_2_wi.json` as the demo released WI source for `CARTONER-ST2`.
- Added `data/released_sources/labeler_fl1_sku_c500_changeover.json` as the demo changeover checklist for `LABELER-FL1 / SKU-C500`.
- Added workflow stages:
  - `retrieve_released_wi_source`
  - `retrieve_changeover_checklist`
  - `resolve_released_source_from_fields`
  - `evaluate_released_source`
  - `released_source_guard`
- Added `source_evaluation` to the gateway response, action loop metadata, and integration event payload.
- Without a released WI or matching SKU checklist, low-control model output is upgraded to `wi_source_required` or `changeover_source_required` and requires human confirmation.

Artifact paths:

- `jetson/released_source.py`
- `data/released_sources/cartoner_station_2_wi.json`
- `data/released_sources/labeler_fl1_sku_c500_changeover.json`
- `tests/test_released_source.py`

### 2026-05-14: Jetson IQC Detector-First Gateway POC

Purpose:

Deploy the IQC detector evidence contract to Jetson and rerun the simulated M400 product-defect POC through the real `/v1/infer` gateway.

Input evidence:

- Image: `docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png`
- Detector JSON field: `detector_evidence_json`
- Product: `AL-HOUSING-L3`
- Detections:
  - `edge_burr`, confidence `0.73`
  - `sealing_face_scratch`, confidence `0.84`
  - `contamination`, confidence `0.79`

Flow check:

```json
{
  "ok": true,
  "has_detector_stage": true,
  "stage_count": 25
}
```

Result:

```text
local_tests=116 passed in 1.00s
HTTP_STATUS=200
latency_ms=45561
analysis_mode=iqc
detector_evidence.status=available
detector_evidence.detection_count=3
quality_evaluation.detector_status=provided
quality_evaluation.status=detector_or_plan_risk_detected
quality_evaluation.recommended_channel=quality_hold
action_card.channel=quality_hold
action_card.priority=high
action_card.owner=quality_engineer
tool_plan.used_tool_calls=2
tool_plan.skipped_tools=["lot_context"]
runtime_stream.closed=true
runtime_last_event=workflow.closed
```

Interpretation:

- This run removed the previous `visual_defect_detector` missing-tool gap.
- Detector output is now an auditable evidence contract, not prompt-only text.
- The quality plan mapped detector findings to released rules:
  - `ALH-BURR-01`: `edge_burr -> expand_inspection`
  - `ALH-SEAL-02`: `sealing_face_scratch -> quality_hold`
  - `ALH-CONTAM-03`: `contamination -> quality_hold`
- The final containment action stayed deterministic: QMS `quality_hold`, owner `quality_engineer`, human confirmation required.

Artifact paths:

- `runtime/iqc-m400-poc/jetson_iqc_detector_poc_response.json`
- `docs/poc-results/iqc-m400-detector-poc-summary.json`
- `docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png`

### 2026-05-14: Jetson IQC M400 Image POC

Purpose:

Run the IQC agent through the real Jetson gateway with a simulated M400 product-defect frame after deploying the quality-plan/evaluator update.

Input image:

```text
docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png
```

The image shows `PRODUCT: AL-HOUSING-L3`, `PLAN: QP-AL-HOUSING-L3 / QP-2026.05-demo`, and visible detector labels:

```text
sealing_face_scratch 0.84
contamination 0.79
edge_burr 0.73
```

Command shape:

```bash
curl -sS -X POST http://127.0.0.1:8081/v1/infer \
  -H "Authorization: Bearer ${DEMO_TOKEN}" \
  -F "analysis_mode=iqc" \
  -F "device_id=m400-iqc-poc" \
  -F "location_hint=line-3-machining-output" \
  -F "capture_mode=iqc_visual_defect_poc" \
  -F "needs_ocr=true" \
  -F "high_detail=true" \
  -F "image=@/tmp/iqc_al_housing_l3_defect_m400.png;type=image/png"
```

Environment:

- Jetson host: `wearedge-pro`
- Gateway: `wearedge-gateway.service`
- Model server: local `llama.cpp` / Gemma 4 E2B
- Visual token budget: `560/560`

Flow check:

```json
{
  "ok": true,
  "has_iqc_quality_plan": true,
  "has_iqc_quality_guard": true,
  "stage_count": 24
}
```

Result:

```text
HTTP_STATUS=200
latency_ms=46460
analysis_mode=iqc
knowledge_base.status=matched
knowledge_base.query_product_id=AL-HOUSING-L3
quality_evaluation.status=visible_risk_needs_detector_review
quality_evaluation.risk_level=medium
quality_evaluation.recommended_channel=quality_hold
action_card.channel=quality_hold
action_card.owner=quality_engineer
integration_event.target=qms_quality_event
runtime_stream.closed=true
runtime_last_event=workflow.closed
```

Key output:

```json
{
  "disposition": "quality_hold",
  "action_card": {
    "channel": "quality_hold",
    "priority": "high",
    "owner": "quality_engineer",
    "integration_target": "qms_quality_event"
  },
  "quality_evaluation": {
    "status": "visible_risk_needs_detector_review",
    "risk_level": "medium",
    "detector_status": "missing_tool_connection",
    "recommended_channel": "quality_hold",
    "findings": [
      "edge_burr -> expand_inspection",
      "sealing_face_scratch -> quality_hold",
      "contamination -> quality_hold"
    ]
  }
}
```

Interpretation:

- The VLM identified visible product defects from the M400 frame.
- IQC quality-plan retrieval matched `AL-HOUSING-L3`.
- Deterministic quality evaluation mapped the visible defect evidence to released plan rules.
- The final QMS action stayed human-confirmed: product is placed on quality hold, not released.

Artifact paths:

- `runtime/iqc-m400-poc/jetson_iqc_poc_response.json`
- `docs/poc-results/iqc-m400-poc-summary.json`
- `docs/assets/iqc-m400-poc/iqc_al_housing_l3_defect_m400.png`

### 2026-05-14 13:55 CST: IQC Detector-First Quality-Plan Guard

Purpose:

Add the second industrial agent hardening step after lao-shi-fu: IQC now uses a released local quality plan and deterministic detector-first evaluation before allowing pass or containment decisions.

Command:

```powershell
& 'C:\Users\ryan hui\anaconda3\python.exe' -m pytest -q
```

Environment:

- Windows workspace: `C:\Users\ryan hui\Documents\New project\WearEdge-Pro`
- Python: Anaconda workspace interpreter
- Runtime path tested with fake model responses and deterministic orchestrator tests

Result:

```text
108 passed in 1.00s
```

Key output:

- Added `data/iqc_quality_plans/al_housing_line3.json` as released demo quality-plan evidence for `AL-HOUSING-L3`.
- Added `jetson/iqc_quality_plan.py` to retrieve product-specific defect rules, detector requirements, sampling scope, and release authority.
- Added `jetson/iqc_quality_eval.py` to block pass without detector evidence, allow pass with `detector clear`, and map defect rules to `expand_inspection`, `quality_hold`, or `stop_production`.
- Added orchestrator stages:
  - `retrieve_iqc_quality_plan`
  - `resolve_iqc_quality_plan_from_fields`
  - `evaluate_iqc_quality_rules`
  - `iqc_quality_guard`
- IQC action cards now carry `quality_evaluation` into the QMS integration payload.

Failures:

- Initial evaluator treated generic `sealing face` context as a defect even when the text said `no visible quality risk`.
- Initial golden scenario for edge burr was upgraded to `quality_hold` because product context included sealing-surface terms.

Fix / follow-up:

- Restricted defect-rule matching to quality observation fields, not product identity text.
- Added explicit clean-pass and insufficient-detector handling.
- Kept detector missing as a review gate unless detector evidence is explicitly provided.

Artifact paths:

- `data/iqc_quality_plans/al_housing_line3.json`
- `jetson/iqc_quality_plan.py`
- `jetson/iqc_quality_eval.py`
- `tests/test_iqc_quality_plan.py`
- `tests/test_iqc_quality_eval.py`

### 2026-05-13: Git Push / Network Baseline

Purpose: confirm project changes can be pushed after proxy/VPN troubleshooting.

Observed:

```text
To https://github.com/davidmillerak2026-sys/WearEdge-Pro.git
   3f4c7a4..88ced18  main -> main
```

Notes:

- Successful proxy path used local proxy port `127.0.0.1:7897`.
- Earlier port `7890` failed because no process was listening.
- This success is useful as the known-good Git/network baseline.

### 2026-05-13: Jetson Gateway Health / Five-Agent Flow

Purpose: confirm Jetson gateway served the five-agent flow after code update.

Observed:

```json
{
  "ok": true,
  "api_version": "wear-edge-infer.v1",
  "supported_modes": ["changeover", "hazard", "iqc", "maintenance", "wi"]
}
```

Important stages confirmed:

```text
normalize_agent
select_agent_route
collect_evidence
bounded_react_tools
build_contract_prompt
model_infer
validate_contract
build_action_card
build_integration_event
close_execution
```

Notes:

- `chmod +x scripts/*.sh` fixed gateway service execution after deploying scripts.
- Windows PowerShell commands such as `sudo`, `chmod`, `rsync`, Linux-style `/tmp`, and `curl -H` caused confusion when run on Windows. Jetson commands must be run in the Jetson SSH shell.

### 2026-05-14 11:25 CST: Maintenance Session Evidence Loop POC

Purpose: verify lao-shi-fu agent can use a multi-step maintenance session instead of one image only.

Input evidence sequence:

```text
maintenance_asset_identity_photo
maintenance_condition_screen_photo
maintenance_temperature_gauge_photo
maintenance_lubrication_record_photo
maintenance_recent_work_record_photo
maintenance_operator_sensory_check
```

Representative result:

```json
{
  "ok": true,
  "analysis_mode": "maintenance",
  "request_id": "ec9d69505ed0409e8347efa599278898",
  "action_card": {
    "channel": "maintenance_report",
    "priority": "medium",
    "owner": "maintenance_engineer"
  },
  "follow_up_plan": {
    "status": "ready_for_human_confirmation",
    "requests": []
  },
  "runtime_stream": {
    "closed": true
  },
  "latency_ms": 48757
}
```

Trace facts:

```text
accepted_evidence_count = 6
contract.ok = true
contract.repaired = false
runtime_stream.closed = true
audit.logged = true
```

Notes:

- This run proved the session/evidence loop was robust.
- At this point maintenance manual/RAG evidence was still being hardened.

### 2026-05-14: Local RAG + Maintenance Evaluation Tests

Purpose: verify local maintenance KB retrieval, deterministic threshold evaluation, and maintenance session API behavior.

Command:

```powershell
& "C:\Users\ryan hui\anaconda3\python.exe" -m pytest
```

Latest local result:

```text
86 passed
```

Covered areas:

```text
industrial-rag-agent contract/retriever/workflow tests
agent loop and route boundary tests
agently orchestrator tests
maintenance KB retrieval tests
maintenance session tests
maintenance signal evaluation tests
FastAPI maintenance session API tests
output contract tests
tool plan and evidence plan tests
```

Important validated behavior:

- `manual_kb` returns matched sections for `PKG-L3-GBX-03`.
- `knowledge_base.thresholds` exposes vibration, temperature, alarm, and lubrication interval thresholds.
- `evaluate_maintenance_thresholds` produces deterministic breaches from accepted session evidence.
- `maintenance_evaluation_guard` can upgrade low-control maintenance actions when high KB threshold breach exists.

### 2026-05-14 12:15 CST: Jetson Deploy With RAG / Evaluation Stage

Purpose: deploy updated tar to Jetson and restart gateway.

Commands used through SSH/SFTP automation:

```bash
scp-equivalent upload:
C:\Users\ryan hui\Documents\New project\WearEdge-Pro\wearedge-pro-latest.tar
  -> ryn@192.168.0.155:/tmp/wearedge-pro-latest.tar

cd ~/WearEdge-Pro
rm -rf /tmp/wearedge-pro-latest
mkdir -p /tmp/wearedge-pro-latest
tar -xf /tmp/wearedge-pro-latest.tar -C /tmp/wearedge-pro-latest
cp -a /tmp/wearedge-pro-latest/. ~/WearEdge-Pro/
chmod +x scripts/*.sh
sudo systemctl restart wearedge-gateway.service
```

Health check confirmed:

```json
{
  "ok": true,
  "eval_stage": {
    "name": "evaluate_maintenance_thresholds",
    "layer": "agent",
    "condition": "mode == maintenance"
  }
}
```

Gateway status:

```text
wearedge-gateway.service active (running)
uvicorn running on http://0.0.0.0:8081
```

### 2026-05-14: Jetson Pytest Availability Check

Purpose: determine whether the full pytest suite can run directly on Jetson.

Observed:

```text
/home/ryn/WearEdge-Pro/.venv/bin/python: No module named pytest
/usr/bin/python3: No module named pytest
```

Conclusion:

- This does not affect real runtime.
- `pytest` is a development/test dependency, not a gateway runtime dependency.
- Runtime validation should use `/healthz`, service status, smoke checks, and `scripts/run_maintenance_session_poc.sh`.

### 2026-05-14: Jetson RAG / Evaluation Smoke Test

Purpose: verify Jetson can import and execute the RAG retrieval and deterministic evaluation code without pytest.

Observed:

```text
matched breach_detected high ['vibration_rms_mm_s', 'gearbox_temperature_c', 'bearing_temperature_c', 'plc_alarm']
```

Meaning:

- KB retrieval worked on Jetson.
- Threshold evaluation worked on Jetson.
- The deterministic evaluator found high-risk condition evidence.

### 2026-05-14: Jetson POC Failure 1 - Context Too Long

Purpose: run full maintenance session POC with RAG and deterministic evaluation in the real gateway path.

Failure:

```text
curl: (22) The requested URL returned error: 502
```

Llama.cpp log:

```text
request (2709 tokens) exceeds the available context size (2048 tokens), try increasing it
```

Root cause:

- RAG snippets plus deterministic evaluation made the prompt too long for the current Jetson llama.cpp server context.
- Current llama.cpp service runs with `-c 2048`.

Fix:

- Compressed maintenance route prompt.
- Reduced KB snippet length.
- Compressed evidence/tool context.
- Kept response/audit fields unchanged.

### 2026-05-14: Jetson POC Failure 2 - Still Slightly Too Long

Observed:

```text
request (2065 tokens) exceeds the available context size (2048 tokens)
```

Root cause:

- The first prompt compression reduced the request from `2709` to `2065` tokens, but still exceeded the 2048-token slot by 17 tokens.

Fix:

- Further shortened maintenance route boundary.
- Reduced KB content snippets to 130 characters.

Follow-up llama.cpp log after fix:

```text
prompt processing done, n_tokens = 940
total time = 40791.47 ms / 1106 tokens
done request: POST /v1/chat/completions 127.0.0.1 200
```

### 2026-05-14: Jetson POC Pass - RAG + Evaluation + Action Card

Purpose: verify end-to-end maintenance session POC after prompt compression.

Result:

```text
Maintenance session POC passed.
Response: /tmp/wearedge-maintenance-session-poc/08_infer_response.json
Trace: /tmp/wearedge-maintenance-session-poc/09_trace.json
```

Summary:

```json
{
  "ok": true,
  "analysis_mode": "maintenance",
  "kb_status": "matched",
  "maintenance_evaluation": {
    "status": "breach_detected",
    "risk_level": "high",
    "breach_count": 5,
    "breach_signals": [
      "vibration_rms_mm_s",
      "gearbox_temperature_c",
      "bearing_temperature_c",
      "plc_alarm",
      "lubrication_interval_days"
    ]
  },
  "action_card": {
    "channel": "maintenance_report",
    "priority": "medium",
    "owner": "maintenance_engineer"
  },
  "integration": {
    "target": "maintenance_work_order",
    "status": "pending_human_confirmation"
  },
  "runtime_closed": true,
  "audit_logged": true,
  "latency_ms": 81096
}
```

Important stages:

```json
[
  {
    "name": "evaluate_maintenance_thresholds",
    "status": "completed",
    "evaluation_status": "breach_detected",
    "risk_level": "high",
    "breach_count": 5
  },
  {
    "name": "build_integration_event",
    "status": "pending_human_confirmation",
    "target": "maintenance_work_order"
  },
  {
    "name": "close_execution",
    "status": "completed"
  }
]
```

Notes:

- A previous valid model run produced `schedule_maintenance`, which is also an acceptable high-breach maintenance work-order channel.
- The POC script was adjusted to allow the high-breach maintenance human-loop channels:
  - `maintenance_report`
  - `schedule_maintenance`
  - `maintenance_escalation`
  - `maintenance_stop`
- Latest run returned `maintenance_report`, which passed the stricter expectation naturally.

### 2026-05-14: Local Lao-Shi-Fu Robustness Tests

Purpose: harden the predictive-maintenance agent against field edge cases before more Jetson POC runs.

Command:

```powershell
& "C:\Users\ryan hui\anaconda3\python.exe" -m pytest tests/test_lao_shi_fu_robustness.py -q
& "C:\Users\ryan hui\anaconda3\python.exe" -m pytest -q
```

Result:

```text
6 passed in 0.06s
92 passed in 0.99s
```

Robustness scenarios covered:

- Sensory-only operator feedback remains `insufficient_evidence` even when a machine KB is matched.
- Numeric readings without a matched maintenance KB cannot produce threshold-breach claims.
- Within-bounds readings remain `condition_monitoring` and do not require human escalation.
- High KB threshold breach upgrades a soft model action such as `Monitor` into `maintenance_report`.
- Unknown machine identity routes to `maintenance_identification_required` before machine-specific advice is trusted.
- Full maintenance-session prompt remains compact enough for the current Jetson context budget guard.

Key conclusion:

- The lao-shi-fu loop is now guarded by contract validation, maintenance KB retrieval, deterministic threshold evaluation, context guard, and maintenance evaluation guard.
- ReAct/RAG evidence can improve the judgment, but final action routing still comes from deterministic rules.

### 2026-05-14: Local Lao-Shi-Fu 10 Realistic Examples

Purpose: generate realistic field-style predictive-maintenance examples and run them through the full deterministic orchestration path.

Command:

```powershell
& "C:\Users\ryan hui\anaconda3\python.exe" -m pytest tests/test_maintenance_kb.py tests/test_lao_shi_fu_realistic_examples.py -q
& "C:\Users\ryan hui\anaconda3\python.exe" -m pytest -q
```

Result:

```text
13 passed in 0.07s
103 passed in 1.00s
```

Generated realistic examples:

```text
normal_green_shift_check
vibration_high_without_alarm
yellow_alarm_no_high_temperature
gearbox_temperature_at_limit
bearing_heat_with_vibration
overdue_lubrication_oil_smell
full_high_risk_schedule_window
wrong_asset_blocks_kb_thresholds
no_asset_plate_blocks_machine_specific_advice
red_trip_with_temperature_spike
```

Important hardening found and fixed:

- Maintenance KB now requires a matching asset identity before applying machine-specific thresholds.
- A wrong asset such as `PKG-L4-GBX-99` no longer matches `PKG-L3-GBX-03` by generic words like gearbox or vibration.
- No readable asset plate blocks machine-specific KB threshold use.
- Insufficient KB/session evidence now blocks low-control maintenance advice and routes to human confirmation.

Key conclusion:

- The 10 examples passed through the same agent loop contracts used by the M400 gateway path.
- The current lao-shi-fu loop is safer than before because RAG cannot accidentally borrow another machine's thresholds.

### 2026-05-14 13:11 CST: Jetson Deploy And Gateway POC After KB Asset Guard

Purpose: deploy the latest lao-shi-fu RAG/guard changes to Jetson and rerun the real gateway maintenance-session POC.

Deploy path:

```text
C:\tmp\wearedge-pro-latest.tar
  -> ryn@192.168.0.155:/tmp/wearedge-pro-latest.tar

Jetson project:
~/WearEdge-Pro
```

Deployment steps:

```bash
cd ~/WearEdge-Pro
rm -rf /tmp/wearedge-pro-latest
mkdir -p /tmp/wearedge-pro-latest
tar -xf /tmp/wearedge-pro-latest.tar -C /tmp/wearedge-pro-latest
cp -a /tmp/wearedge-pro-latest/. ~/WearEdge-Pro/
chmod +x scripts/*.sh
sudo systemctl restart wearedge-gateway.service
```

Gateway health:

```text
/healthz OK after gateway restart
```

POC command:

```bash
cd ~/WearEdge-Pro
source .env
DEMO_TOKEN="$DEMO_TOKEN" GATEWAY_WAIT_SECONDS=90 scripts/run_maintenance_session_poc.sh
```

Result:

```text
Maintenance session POC passed.
Response: /tmp/wearedge-maintenance-session-poc/08_infer_response.json
Trace: /tmp/wearedge-maintenance-session-poc/09_trace.json
```

Summary:

```json
{
  "ok": true,
  "analysis_mode": "maintenance",
  "request_id": "ad56c0251a8c4ac1a18584ed74c0cf20",
  "kb_status": "matched",
  "kb_asset": "PKG-L3-GBX-03",
  "maintenance_evaluation_status": "breach_detected",
  "maintenance_risk_level": "high",
  "maintenance_breach_count": 5,
  "maintenance_breach_signals": [
    "vibration_rms_mm_s",
    "gearbox_temperature_c",
    "bearing_temperature_c",
    "plc_alarm",
    "lubrication_interval_days"
  ],
  "action_channel": "maintenance_report",
  "action_owner": "maintenance_engineer",
  "action_priority": "medium",
  "integration_target": "maintenance_work_order",
  "integration_status": "pending_human_confirmation",
  "runtime_closed": true,
  "latency_ms": 78063,
  "session_evidence_count": 6,
  "trace_event_count": 8
}
```

Important stage:

```json
{
  "name": "maintenance_evaluation_guard",
  "status": "completed",
  "evaluation_status": "breach_detected",
  "risk_level": "high",
  "final_channel": "maintenance_report"
}
```

Key conclusion:

- The latest KB asset guard deployed cleanly to Jetson.
- The real gateway path still closes the M400 maintenance-session loop.
- RAG matched the correct asset `PKG-L3-GBX-03`, deterministic evaluation found five breaches, and the final action stayed human-confirmed through CMMS work-order routing.

### 2026-05-19 CST: M400 One-Tap Field Launch

Purpose:

Remove on-glasses typing from the M400 WearEdge workflow. Operators should launch the app, wait for Jetson connection/session readiness, capture a photo, and run the lao-shi-fu session step without entering gateway URL, token, mode, or capture metadata.

Implementation:

- Added build-time gateway/token defaults for the Android APK so the demo token is injected during build rather than typed on the device.
- Changed the M400 default route to `analysis_mode=maintenance` and `capture_mode=m400-lao-shi-fu-session`.
- Hid gateway URL, token, device, capture mode, session, evidence type, summary, and fields JSON behind an `Advanced` panel.
- Added startup auto-connect: app launch now calls Jetson health and creates a maintenance session automatically.
- Simplified the visible field UI to `Capture Photo`, `Run Lao-Shi-Fu`, `Retry Jetson`, and `Trace Session`.
- Updated capture completion status to direct the operator to `Run Lao-Shi-Fu` after a JPEG is available.

Verification:

```text
Windows Gradle build with build-time demo token: BUILD SUCCESSFUL
APK: clients/m400/android/app/build/outputs/apk/debug/app-debug.apk
ADB device availability during this build: no M400 attached, so APK install/live retry remains pending.
```

### 2026-05-18 10:39 CST: M400 Lao-Shi-Fu Session Loop Client Wiring

Purpose:

Implement the product behavior required for a real M400-to-Jetson lao-shi-fu evidence loop: M400 captures an initial frame, Jetson returns specific missing evidence, M400 keeps the same `session_id`, uploads follow-up evidence, and Jetson reruns the maintenance agent until the follow-up queue is clear.

Implementation:

- Added Android client calls for `POST /v1/maintenance-sessions`, `POST /v1/maintenance-sessions/{session_id}/evidence`, `POST /v1/maintenance-sessions/{session_id}/infer`, and `GET /v1/maintenance-sessions/{session_id}/trace`.
- Added M400 UI controls: `Start Session`, `Lao-Shi-Fu Session Step`, `Trace Session`, `Evidence type`, `Evidence summary`, and `Fields JSON`.
- Added session fields to the M400 result parser: `session_id`, accepted evidence IDs, requested evidence IDs, missing requested evidence IDs, and evidence count.
- Added voice/ADB command mappings for `start session`, `session step`, `next evidence`, `run lao shi fu`, and `trace session`.
- Added foreground `am start --activity-single-top` automation extras for reliable M400 debug configuration without typing long values on-device.
- Added logcat status tag `WearEdgeM400Demo` and a headless Camera2 `ImageReader` fallback when the preview `TextureView` is unavailable.

Verification:

```text
Windows Gradle build: BUILD SUCCESSFUL
ADB install to M400 M005043620: Success
M400 configuration intent: WearEdgeM400Demo: M400 demo configuration loaded.
M400 custom phrase registration includes: start session, session step, next evidence, run lao shi fu, trace session.
M400 Check Gateway command: Gateway health OK.
M400 Start Session command: Session created.
```

Current blocker:

During ADB-driven capture on this M400 state, Android rejected camera open before the first session evidence upload:

```text
CAMERA_DISABLED: Caller "com.wearedge.m400demo" cannot open camera "0" from background
Session Step: Capture a JPEG before running the lao-shi-fu session step.
```

The app was installed and the new session loop compiled. The M400-to-Jetson health check and session creation path are live. The full iterative run still needs to be retried with the WearEdge app visibly foregrounded on the glasses so Camera2 can capture a JPEG, then `Lao-Shi-Fu Session Step` can add evidence and run `/v1/maintenance-sessions/{session_id}/infer`.

Artifact paths:

- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/WearEdgeM400Client.kt`
- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/MainActivity.kt`
- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/WearEdgeVoiceAdapter.kt`
- `clients/m400/android/README.md`

### 2026-05-20 CST: M400 0.3.18 Final Action Workspace Alignment

Purpose:

Align the Windows workspace after the M400 worn field-test loop so code, documentation, and evidence point to the same product baseline.

Implementation:

- Advanced the Android client evidence flow to `0.3.18-m400-a11-final-actions`.
- Added full-screen final conclusion display on M400.
- Added simulated external follow-up action confirmations for supervisor email, line-stop request, and planned downtime placeholder.
- Updated voice behavior so `accept` can confirm photo preview or final follow-up actions, while `reject` / `retake` can discard preview or skip a follow-up action.
- Made operator sensory completion enter `FINAL ANALYZING` and auto-submit the final context frame.
- Made connection reset recover visibly through retry preview instead of failing silently.
- Aligned `docs/m400-field-test-learnings.md`, `docs/m400-lao-shi-fu-field-test-playbook.md`, and `docs/m400-workspace-alignment-2026-05-20.md`.

Verification:

```text
Windows Gradle build: BUILD SUCCESSFUL
ADB install to M400 M005043620: Success
dumpsys package versionCode=20
dumpsys package versionName=0.3.18-m400-a11-final-actions
APK: clients/m400/android/app/build/outputs/apk/debug/app-debug.apk
```

Evidence:

- `docs/poc-results/m400-worn-comparison-20260520-181119/m400-log-crawl-report-20260520-181119.md`
- `docs/poc-results/m400-worn-comparison-20260520-181119/field-test-summary-20260520-181119.md`
- `docs/poc-results/m400-worn-comparison-20260520-181119/voice-dialogue-timeline-20260520-181119.log`
- `docs/poc-results/m400-worn-comparison-20260520-181119/camera-upload-timeline-20260520-181119.log`
- `docs/poc-results/m400-worn-comparison-20260520-181119/jetson-agent-response-extract-20260520-181119.log`
- `docs/poc-results/m400-worn-comparison-20260520-181119/ui-visible-text-timeline-20260520-181119.md`

### 2026-05-20 CST: M400 Field Benchmark Ledger Refresh

Purpose:

Record the May 18-20 M400 and PB551 benchmark progression in judge-facing form: latency, memory, power, visual token budget, and stability improvements.

Recorded metrics:

- Real M400 high-detail maintenance calls from 2026-05-18 to 2026-05-20: 7 measured calls, min `44907 ms`, max `46778 ms`, average `45827 ms`.
- Worn M400 evidence-loop measured turns from 2026-05-20: `45456 / 45836 / 46275 / 46415 ms`, average `45996 ms`.
- Visual token budget for the M400 lao-shi-fu maintenance route: `LLAMA_IMAGE_MIN_TOKENS=560`, `LLAMA_IMAGE_MAX_TOKENS=560`.
- PB551 low-battery patrol: 12 patrol requests, average `4.728 s`; maintenance avg `5.779 s`, WI avg `4.342 s`, IQC avg `4.064 s`.
- PB551 low-battery power estimate: `36% -> 24%` over `57.65 min`, about `9.0W`, with no observed undervoltage, NVMe reset, thermal throttle, OOM, or abnormal shutdown.
- PB551 same-day M400 debug observation: `100% -> 34%` over about `5.62h`, estimated average `8.46W`.
- Jetson memory envelope from patrol snapshots: RAM around `5.62-5.71GB / 7.62GB`, swap around `798-835MB / 3.81GB`.

Updated artifact:

- `docs/edge-runtime-benchmark.md`

## Current Jetson Validation Command

Use this on Jetson for the current lao-shi-fu full session validation:

```bash
cd ~/WearEdge-Pro
source .env
chmod +x scripts/*.sh
DEMO_TOKEN="$DEMO_TOKEN" GATEWAY_WAIT_SECONDS=90 scripts/run_maintenance_session_poc.sh
```

Expected terminal ending:

```text
Maintenance session POC passed.
Response: /tmp/wearedge-maintenance-session-poc/08_infer_response.json
Trace: /tmp/wearedge-maintenance-session-poc/09_trace.json
```

Expected response assertions:

```text
.ok == true
.analysis_mode == "maintenance"
.knowledge_base.status == "matched"
.maintenance_evaluation.status == "breach_detected"
.maintenance_evaluation.risk_level == "high"
.maintenance_evaluation.breaches | length >= 3
.action_card.channel in maintenance human-loop channels
.integration_event.target == "maintenance_work_order"
.runtime_stream.closed == true
```

## Known Runtime Caveats

1. Jetson does not currently have `pytest` installed. This is acceptable for runtime, but not enough for on-device unit-test execution.
2. Current llama.cpp context is `2048`; prompt growth must be watched carefully when adding more RAG sections or evidence text.
3. Full multimodal POC latency is around 80 seconds on the current Jetson path. This is expected for the current Orin Nano + llama.cpp + Gemma E2B + visual token setup.
4. The 2TB SSD helps storage, model files, KB indexes, logs, and cached artifacts, but does not directly increase inference speed.

## Append Template

```markdown
### YYYY-MM-DD HH:mm CST: <Test Name>

Purpose:

Command:

Environment:

Result:

Key output:

Failures:

Fix / follow-up:

Artifact paths:
```
