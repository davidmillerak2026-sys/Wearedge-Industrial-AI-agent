# WearEdge Pro Jetson Edge Runtime Benchmark

Snapshot date: 2026-05-20

This document turns the existing Jetson PoC logs into a benchmark and learning ledger for the Gemma 4 hackathon submission. The goal is to prove that WearEdge Pro is running a real edge deployment, while staying honest about what has been measured, what is only script-ready, and what still needs a fresh Jetson run.

## Judge Takeaway

WearEdge Pro has already shown a working local path on Jetson Orin Nano 8GB:

```text
M400 / Web image
  -> Jetson FastAPI gateway :8081
  -> local llama.cpp server :8080
  -> Gemma 4 E2B Q4_K_S + mmproj-F16
  -> structured action card
  -> audit log / runtime stream / integration event
```

The strongest current proof points are:

- A 3.17 MB industrial JPEG completed local Gemma 4 E2B vision inference in `5824 ms`.
- The same demo path still worked after Jetson reboot and systemd autostart, with `8734 ms` image inference.
- Six recorded safety/contract runs sit between `3503 ms` and `13205 ms`, average `8579 ms`.
- A high-detail lao-shi-fu maintenance route with `LLAMA_IMAGE_MIN_TOKENS=560` and `LLAMA_IMAGE_MAX_TOKENS=560` read machine identity, vibration, temperature, alarm, lubrication, maintenance record, and operator sensory evidence.
- The intentionally heavy 7-turn prompt-carried maintenance run exposed a slow path: 7 model calls averaged `42187 ms`, with a max of `48568 ms`.
- The final fixed maintenance rechecks dropped back to `7470-7646 ms`, proving the 48s path was mostly caused by prompt-carried evidence and high-detail context, not by the endpoint being fundamentally unusable.
- Real M400 field runs are now archived. Across seven real-M400 high-detail maintenance calls from 2026-05-18 to 2026-05-20, measured Jetson inference latency ranged from `44907 ms` to `46778 ms`, average `45827 ms`.
- The 2026-05-20 worn M400 evidence loop proved stability improvement: visual gaps reduced from `6 -> 5 -> 4 -> 3 -> 2 -> operator sensory`, operator voice answers were captured one-by-one, and the remaining post-sensory bug was fixed in Android `0.3.18-m400-a11-final-actions`.
- Mobile power is no longer only theoretical: PB551 low-battery patrol ran from `36%` to `24%` for `57.65 min`, averaging about `9.0W`, with services still active and no observed undervoltage, NVMe reset, thermal throttle, OOM, or abnormal shutdown.

## Measurement Rules

| Rule | Meaning |
| --- | --- |
| `latency_ms` source | Uses the response fields preserved in `docs/poc-results/` and `runtime/complete-lao-shi-fu-run*`. |
| Included work | Gateway request handling, local llama.cpp model call, output contract parsing, action card / runtime stream generation where present. |
| Not included | M400 camera capture time, physical wearer interaction time, mobile UI rendering, and real plant Wi-Fi variance unless explicitly captured later. |
| Token budget note | Older hazard JSON does not persist `modality_plan`; the configured default launcher route is `70/70`, while the maintenance PoC explicitly records `560/560`. |
| Evidence status | `Measured` means a Jetson response or report has a concrete value. `Script-ready` means the repo has a command but the latest numeric Jetson result is not yet archived. |

## Runtime Baseline

| Layer | Current baseline | Evidence |
| --- | --- | --- |
| Edge device | Jetson Orin Nano 8GB Developer Kit | `docs/hardware-baseline.json`, `docs/core-bom.md` |
| OS | JetPack 6.2.1 / L4T R36.4.4, Ubuntu 22.04, aarch64 | `docs/gemma4-e2b-poc-summary.md` |
| Storage | 2TB M.2 NVMe, target mount `/mnt/nvme` | `docs/hardware-baseline.json` |
| Text model | `gemma-4-E2B-it-Q4_K_S.gguf`, `3043932288` bytes, SHA256 `0a2fac16...50c99` | `docs/gemma4-e2b-model-manifest.lock` |
| Vision projector | `mmproj-F16.gguf`, `985654080` bytes, SHA256 `140be8d7...215fa` | `docs/gemma4-e2b-model-manifest.lock` |
| Inference server | `llama-server` on `0.0.0.0:8080`, CUDA backend, `-ngl 99`, context `2048` | `scripts/run_llama_server.sh` |
| Product gateway | FastAPI on `0.0.0.0:8081` | `scripts/run_fastapi.sh`, `docs/e2b-deployment-runbook.md` |
| Device mode | `wearedge-llama.service` and `wearedge-gateway.service` enabled and active after reboot | `docs/gemma4-e2b-poc-summary.md` |
| Privacy default | Audit metadata can be logged; original image is not saved unless upload caching is explicitly enabled | `docs/technical-evidence.md` |

## Benchmark Summary Table

| Scenario | Evidence status | Input / mode | Visual tokens | Latency | Result | What it proves |
| --- | --- | --- | --- | ---: | --- | --- |
| First Jetson image PoC | Measured | 3.17 MB JPEG, hazard-style `scene/risk/action` | Default launcher route, treated as `70/70` | `5824 ms` | `ok=true`, local Gemma 4 response | Jetson can perform real local image+text inference without cloud API. |
| Browser retry after systemd reboot | Measured | Same 3.17 MB JPEG after reboot | Default launcher route, treated as `70/70` | `8734 ms` | `ok=true`, `validated_after_reboot=true` | The edge node survives reboot and is not a one-terminal demo. |
| Contract hardening loop | Measured | Same hazard image, 3 repeated runs | Default launcher route, treated as `70/70` | `13205 / 3503 / 10322 ms` | `contract.ok=true`, `violations=[]` each time | The gateway can repair unstable model format and still return machine-readable fields. |
| Smoke test with audit | Measured | 3.17 MB JPEG, M400-like metadata | Default launcher route, treated as `70/70` | `9884 ms` | `request_id=5b33...c8f`, `audit.logged=true`, `saved_path=null` | The system can trace a device request while keeping source images off disk by default. |
| Maintenance initial high-detail frame | Measured | 2.66 MB PNG, `analysis_mode=maintenance` | `560/560` | `8390 ms` | `schedule_maintenance`, `contract.ok=true` | High-detail vision can read machine identity, temperature, vibration, and warning context. |
| Maintenance prompt-carried full sequence | Measured | 7 M400-style turns with accepted evidence carried in prompt | `560/560` | avg `42187 ms`, max `48568 ms` | 7/7 contract pass, 7/7 runtime closed | The slow path is measurable and explains why session state is needed. |
| Maintenance final code recheck | Measured | Initial frame and final sensory-check frame after action-starter fix | POC route recorded as `560/560` | `7470 / 7646 ms` | `condition_inspection` then `maintenance_stop` | The deterministic Chinese action-starter fix stabilized the final decision path. |
| Five-agent software matrix | Measured, non-latency | Maintenance, IQC, changeover, WI, hazard | N/A | N/A | `5/5 passed`, golden `25/25 passed` | The runtime action envelope is deterministic across routes before plant/M400 trials. |
| Maintenance session evidence API | Script-ready and locally tested | Create session, upload six evidence items, infer, trace | High-detail final infer | Jetson numeric run still needs archive | Last local result documented as `86 passed` | Moves evidence out of prompt stuffing and into Jetson-owned session state. |

## Real M400 Field Benchmark Progression

This table is the judge-facing "we kept improving it" record. It separates model latency from field stability, because the biggest May 18-20 gains were not raw speed; they were removing typing, removing stale sessions, making voice interaction predictable, preserving evidence, and making failure recovery visible.

| Date | App / run | Interaction path | Visual tokens | Measured latency | Memory / power evidence | Stability result | Improvement captured |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| 2026-05-18 | Real M400 full chain | Manual M400 UI: `Check Gateway -> Capture Camera2 JPEG -> Upload -> Audit Recent` | `560/560` high-detail maintenance route | `44907 ms` | PB551 same-day debug observation: about `8.46W` average over `5.62h` mixed Jetson/M400 debug day | PASS: `request_id` matched audit; upload JPEG saved to NVMe | First real M400 -> Wi-Fi -> Jetson -> local Gemma -> M400 result loop. |
| 2026-05-18 | WearEdge Voice Adapter | ADB/adapter command path: `maintenance -> health -> capture -> upload -> audit` | `560/560` route observed through maintenance response | `46778 ms` | Same Jetson/PB551 environment; power not separately sampled during this short run | PASS: app-level command bridge completed inference and audit match | Added controlled command surface without changing Gateway API. |
| 2026-05-18 | Vuzix custom phrase upload | Native Vuzix phrase: `check gateway`, `capture frame`, `maintenance mode`, `upload to Jetson` | `560/560` route observed through maintenance response | `45122 ms` | Same Jetson/PB551 environment; power not separately sampled during this short run | PASS: protected Vuzix action boundary confirmed; custom phrase upload completed | Replaced button-only flow with Vuzix speech phrase integration. |
| 2026-05-19 | Real voice regression | Three real voice passes plus patch verification | `560/560` maintenance session route | Qualitative; per-run latency not summarized | M400/Jetson same LAN; no power sampling in run folder | MIXED -> FIXED: found stale session restore, busy command queue, delayed voice broadcast; verified recovery/cooldown fixes | Stability moved from "works once" to repeatable field-loop behavior under repeated voice input. |
| 2026-05-20 | Worn comparison run | Worn M400: `capture photo -> preview -> accept -> Jetson` repeated through six visual evidence turns, then sensory voice Q&A | `560/560`; `LLAMA_IMAGE_MIN_TOKENS=560`, `LLAMA_IMAGE_MAX_TOKENS=560` recorded in responses | Measured turns: `45456 / 45836 / 46275 / 46415 ms`; avg `45996 ms` | Jetson memory/power not sampled in this folder; use PB551 patrol baseline below for system envelope | PARTIAL PASS: visual evidence loop and sensory Q&A worked; post-sensory context preview had state mismatch | Led directly to `0.3.18`: full-screen conclusion, auto final analyzing, retry-visible connection reset, and confirmable follow-up actions. |

Real-M400 latency stats from archived runs:

| Set | Count | Min | Max | Average |
| --- | ---: | ---: | ---: | ---: |
| Real M400 high-detail calls, 2026-05-18 to 2026-05-20 | 7 | `44907 ms` | `46778 ms` | `45827 ms` |
| Worn M400 evidence-loop measured turns, 2026-05-20 | 4 | `45456 ms` | `46415 ms` | `45996 ms` |

Interpretation:

- The current real-M400 lao-shi-fu path prioritizes OCR/HMI/readable-evidence quality with `560/560` visual tokens, so it is slower than the static patrol smoke path.
- The important 2026-05-20 progress was stability and operator workflow: one preview confirmation gate, iterative evidence reduction, one-question sensory capture, and final recovery/follow-up actions.
- The next speed milestone should benchmark `280/280` and `140/140` on the same M400 images, then choose the lowest token budget that still reads asset IDs, HMI, gauges, and maintenance records.

## Safety / Hazard Latency Set

These runs are the clearest current "edge is real" latency set because they use the same 3.17 MB industrial image family and are recorded as direct Jetson results.

| Run | Source | Image bytes | Latency | Contract / output status |
| --- | --- | ---: | ---: | --- |
| Safety sample | `docs/poc-results/gemma4-e2b-safety-sample-result.json` | `3170693` | `5824 ms` | `ok=true`, structured answer |
| Autostart browser check | `docs/poc-results/gemma4-e2b-autostart-browser-result.json` | `3170693` | `8734 ms` | `ok=true`, reboot validated |
| Contract stability 1 | `docs/gemma4-e2b-poc-summary.md` | `3170693` | `13205 ms` | `contract.ok=true`, repaired |
| Contract stability 2 | `docs/gemma4-e2b-poc-summary.md` | `3170693` | `3503 ms` | `contract.ok=true`, no repair |
| Contract stability 3 | `docs/gemma4-e2b-poc-summary.md` | `3170693` | `10322 ms` | `contract.ok=true`, repaired |
| Audit smoke | `docs/gemma4-e2b-poc-summary.md`, `docs/technical-evidence.md` | `3170693` | `9884 ms` | `audit.logged=true`, `saved_path=null` |

Summary:

| Count | Min | Max | Average |
| ---: | ---: | ---: | ---: |
| 6 | `3503 ms` | `13205 ms` | `8579 ms` |

## Visual Token Budget Table

| Budget | Current evidence | Latency evidence | Quality note | Decision |
| --- | --- | --- | --- | --- |
| `70/70` | Default launcher budget in `scripts/run_llama_server.sh`; older hazard result JSON does not persist the budget field. | Hazard/safety set: `3503-13205 ms`, avg `8579 ms`. | Good for coarse safety scenes, trip/fall/debris risk, short action card. Not enough to rely on small HMI text or asset labels. | Keep as fast safety/default demo path. |
| `140/140` | Not yet archived as a Jetson numeric run. | Missing. | Candidate midpoint for M400 wearable UX. | Needs controlled benchmark. |
| `280/280` | Not yet archived as a Jetson numeric run. | Missing. | Candidate balance for readable labels without full `560/560` cost. | Needs controlled benchmark. |
| `560/560` | Explicitly recorded in `docs/five-agent-poc-validation.md`, `docs/lao-shi-fu-maintenance-poc.md`, and 2026-05-20 M400 response extracts. | Maintenance final rechecks `7470-7646 ms`; prompt-carried 7-turn full sequence avg `42187 ms`; real M400 field calls avg `45827 ms`. | Best current route for machine identity, HMI values, alarms, temperature gauges, and records. | Use for judge demo when detail matters; avoid prompt stuffing and benchmark lower budgets next. |

Next controlled benchmark should run the same image set at `70/140/280/560`, recording latency, answer quality, memory, temperature, and whether OCR-like details are preserved.

## Memory, Power, And Thermal Envelope

The field M400 folders primarily capture interaction and Jetson response logs. Power and memory evidence comes from the controlled PB551 patrol runs, which use the same Jetson services, model files, NVMe upload path, and gateway.

| Run | Workload | Memory / swap observation | Power / thermal observation | Latency / stability result | Evidence |
| --- | --- | --- | --- | --- | --- |
| PB551 idle baseline, 2026-05-15 | 25W mode, services active, 120s idle, 256MiB NVMe write | `tegrastats` captured live; memory not summarized in JSON | PB551 idle VDD_IN steady about `4.36-4.44W`, warmup peak about `6.29W`; temperature about `46.6-48.3C`; NVMe write `661 MB/s` | Services active; `/healthz` OK; no undervoltage/NVMe reset/thermal/OOM/shutdown logs | `docs/hardware-baseline.json`, `docs/hardware-milestones.md` |
| PB551 low-battery 60-minute patrol, 2026-05-15 | 1 text health, 2 warm-up image requests, 12 rotating maintenance/WI/IQC requests | `tegrastats` snapshots showed RAM around `5.62-5.71GB / 7.62GB`, swap around `798-835MB / 3.81GB` during late patrol windows | PB551 `36% -> 24%` over `57.65 min`, estimated `9.0W`; temperatures about `47-50.6C`; idle VDD_IN about `4.39-4.47W`, post-inference about `5.71-5.79W` | 15/15 requests completed, HTTP 200, contracts OK, audit logged, services active after run | `docs/hardware-baseline.json`, `docs/hardware-milestones.md` |
| PB551 M400 debug day, 2026-05-18 | Jetson boot, service repair, model restore, M400 upload, audit, network troubleshooting | Memory not separately sampled in the final observation | PB551 `100% -> 34%` over about `5.62h`, estimated average `8.46W`, estimated remaining runtime `2.89h` at same average power | Jetson continued running; router outage was network infrastructure, not Jetson shutdown evidence | `docs/hardware-baseline.json`, `docs/hardware-milestones.md` |

Power interpretation:

- The edge compute box is currently operating in a practical `8.5-9.0W` average field-debug envelope, despite being configured in Jetson `25W` mode.
- Short inference pulses in `tegrastats` are visible around `5.7-5.8W VDD_IN`; long-run average is higher because it includes conversion losses, idle time, services, Wi-Fi, NVMe, and battery percentage granularity.
- No evidence yet claims 20% battery and below, cable-shake robustness, enclosed thermal rise, or full simultaneous model + NVMe stress.

## Lao-shi-fu Maintenance Sequence

The 7-turn POC intentionally carried accepted evidence in the prompt. That makes it valuable as a stress test, not as the desired live SLA.

| Step | Capture | Size | Latency | Channel | Priority | Learning |
| ---: | --- | ---: | ---: | --- | --- | --- |
| 0 | Initial full frame | `2.66 MB` | `8390 ms` | `schedule_maintenance` | medium | One high-detail frame can identify the asset context and request bounded follow-up evidence. |
| 1 | Asset identity | `0.09 MB` | `48129 ms` | `condition_inspection` | low | Small image size did not make the run fast because the prompt already carried accumulated context. |
| 2 | Condition screen | `0.11 MB` | `46295 ms` | `maintenance_stop` | critical | HMI / condition monitor evidence can drive maintenance escalation. |
| 3 | Temperature gauges | `0.09 MB` | `48568 ms` | `maintenance_stop` | critical | Temperature evidence confirms machine-condition risk without claiming final root cause. |
| 4 | Lubrication record | `0.12 MB` | `48002 ms` | `condition_inspection` | low | A record photo is evidence, not an automatic stop; it must be combined with live condition data. |
| 5 | Recent work record | `0.12 MB` | `47413 ms` | `maintenance_stop` | critical | History prevents the agent from treating a condition image as an isolated event. |
| 6 | Operator sensory check | `0.15 MB` | `48513 ms` | `maintenance_stop` | critical | Human sensory observations can escalate risk while still requiring technician confirmation. |

Sequence stats:

| Count | Min | Max | Average |
| ---: | ---: | ---: | ---: |
| 7 | `8390 ms` | `48568 ms` | `42187 ms` |

Final fixed-code recheck:

| Check | Latency | Channel | Priority | Learning |
| --- | ---: | --- | --- | --- |
| Initial full frame | `7470 ms` | `condition_inspection` | low | With the narrowed action normalizer deployed, the first frame stays bounded instead of over-escalating. |
| Operator sensory check | `7646 ms` | `maintenance_stop` | critical | With enough evidence and the `Stop` action starter normalized, the final maintenance stop is stable. |

## Milestones And Learnings

| Milestone | Evidence | Learning captured |
| --- | --- | --- |
| Hardware baseline fixed | Jetson Orin Nano 8GB + 2TB NVMe in `docs/hardware-baseline.json` and `docs/core-bom.md`. | The SSD is essential for model files, logs, cached images, and KB indexes; it does not materially increase token generation speed. |
| JetPack / L4T baseline verified | JetPack 6.2.1 / L4T R36.4.4 recorded in PoC docs. | A stable OS baseline matters more than chasing larger models early. |
| Network recovery path found | `docs/network-troubleshooting.md`, deployment notes. | HF/GitHub large downloads can fail on Jetson; Windows download plus manual transfer is a valid recovery path. |
| llama.cpp CUDA path compiled | `scripts/build_llama_cpp.sh`, `scripts/run_llama_server.sh`. | CUDA env vars and `nvcc` path must be explicit on Jetson. |
| Model manifest locked | `docs/gemma4-e2b-model-manifest.lock`. | Large GGUF binaries stay out of Git; reproducibility comes from filename, bytes, SHA256, and model directory. |
| Q4_K_S route selected | `docs/e2b-deployment-runbook.md`, `docs/core-bom.md`. | Q4_K_S + `mmproj-F16` is the current 8GB Orin Nano delivery route; Q8/E4B are comparison candidates, not first demo baseline. |
| llama-server text health added | `scripts/smoke_test.sh`. | A visible short text answer catches server/template failures before image tests. |
| FastAPI gateway created | `jetson/app.py`, `docs/m400-inference-contract.md`. | The model server should stay behind a product gateway that owns auth, request ids, contracts, audit, and device metadata. |
| First local image PoC completed | `5824 ms` safety sample in `docs/poc-results/`. | This is the core proof that WearEdge Pro is not a cloud API wrapper. |
| systemd autostart validated | `8734 ms` post-reboot browser result; services enabled/active. | The demo can be device-like: reboot, wait, health check, upload. |
| Output contract hardened | `jetson/output_contract.py`, `tests/test_output_contract.py`. | Industrial systems need fields, not loose paragraphs. |
| Contract repair loop measured | 3 repeated contract runs in `docs/gemma4-e2b-poc-summary.md`. | Repair adds latency, but it converts model drift into explicit engineering behavior. |
| M400 request metadata added | `/v1/infer` contract returns `api_version`, `request_id`, and `device`. | Every wearable frame needs a traceable id for UI, audit, and work-order mapping. |
| Privacy-first audit proven | `request_id=5b33...c8f`, `saved_path=null`. | The project can keep audit metadata without storing factory images by default. |
| Five-agent route matrix passed | `5/5 passed`, golden `25/25 passed` in `docs/five-agent-poc-validation.md`. | Agent routing must be bounded by industrial mode; maintenance should not drift into EHS hazard logic. |
| High-detail maintenance route proven | `560/560` lao-shi-fu POC. | Small text, HMI, labels, alarms, and gauges need a higher visual token budget than coarse hazard scenes. |
| Chinese action starter bug found and fixed | `docs/lao-shi-fu-maintenance-poc.md`. | Multilingual model outputs need deterministic action normalization, not English-only validation. |
| Full 7-turn maintenance POC completed | Runtime summary under `runtime/complete-lao-shi-fu-run-final/`. | Prompt-carried evidence works, but the 48s slow path makes it unsuitable as the final M400 live flow. |
| Maintenance session state introduced | `docs/maintenance-session-evidence-loop.md`, `jetson/maintenance_session.py`. | Jetson should own accumulated evidence, trace, and missing evidence state instead of stuffing every prior turn into the model prompt. |
| Local maintenance KB and threshold evaluator added | `data/maintenance_kb/pkg_l3_gbx_03.json`, `jetson/maintenance_kb.py`, `jetson/maintenance_signal_eval.py`. | Vibration, temperature, PLC alarm, and lubrication breaches should be deterministic evidence before model explanation. |
| M400 Android MVP compiled | `clients/m400/android/` docs and project status. | The wearable app has a buildable client, but true M400 camera/network/UX validation remains a major open risk. |
| Real M400 single-request full chain passed | `docs/poc-results/m400-real-device-full-chain-2026-05-18/`. | Camera2, Wi-Fi, Jetson local inference, M400 display, and audit match are no longer hypothetical. |
| M400 voice adapter and Vuzix phrase path passed | `docs/poc-results/m400-voice-adapter-2026-05-18/`, `docs/poc-results/m400-custom-voice-phrases-2026-05-18/`. | The project moved from touch UI to controlled voice command surfaces without changing the Gateway contract. |
| Real voice regression fixed stale-session and delayed-command failures | `docs/poc-results/m400-real-voice-regression-20260519-163838/`, `docs/m400-field-test-learnings.md`. | Field usability improved by measuring failures, then adding session validation, cooldown, and command gating. |
| Worn M400 multi-evidence loop measured | `docs/poc-results/m400-worn-comparison-20260520-181119/`. | The app can reduce evidence gaps across repeated photos and collect operator sensory answers; finalization bug led to 0.3.18 fix. |
| Benchmark document refreshed | This file. | The benchmark now covers latency, token budget, memory/power envelope, and stability progression. |

## Current Gaps Before A Stronger Submission Claim

| Gap | Why it matters | Next artifact |
| --- | --- | --- |
| Synchronized `tegrastats` during live M400 worn run | Judges need memory, GPU, CPU, and temperature at the exact same time as wearable inference, not only patrol baselines. | Add a future `docs/poc-results/m400-live-tegra-*.txt` captured while the glasses are running. |
| Controlled `70/140/280/560` visual-token matrix | Shows tradeoff between speed and OCR/HMI quality. | Add a benchmark table using the same image set and same prompt. |
| Cold-start timing | Demonstrates how long after boot the demo is ready. | Record service startup, first health pass, first image pass. |
| Lower-latency M400 route | The current real-M400 high-detail maintenance loop averages about `45.8s`, which is acceptable for proof but slow for routine operation. | Benchmark `140/140` and `280/280` on the same M400 images and record quality loss. |
| Final 0.3.18 worn regression | The 0.3.18 code fixes the 0.3.17 post-sensory finalization bug, but the fix still needs a worn device run. | Archive a new field folder with full-screen conclusion and accepted simulated follow-up actions. |

## Recommended Next Benchmark Command Set

Run this on Jetson before recording the demo:

```bash
systemctl is-active wearedge-llama.service
systemctl is-active wearedge-gateway.service
ss -ltnp | grep -E ':(8080|8081)'
curl -s http://127.0.0.1:8081/healthz | jq .
tegrastats --interval 1000
```

Then run the fixed-image smoke test:

```bash
cd ~/WearEdge-Pro
source .env
TEST_IMAGE=/home/ryn/WearEdge-Pro/testdata/unsafety.jpeg \
DEMO_TOKEN="$DEMO_TOKEN" \
scripts/smoke_test.sh
```

For the maintenance session flow:

```bash
cd ~/WearEdge-Pro
source .env
GATEWAY_WAIT_SECONDS=90 \
DEMO_TOKEN="$DEMO_TOKEN" \
scripts/run_maintenance_session_poc.sh
```

Archive the final response and trace into `docs/poc-results/` only after removing local tokens and machine-specific private paths.

## Submission Language

Use this benchmark claim in judge-facing material:

```text
WearEdge Pro runs Gemma 4 E2B locally on Jetson Orin Nano 8GB. Recorded Jetson image inference ranges from 3.5s to 13.2s for the current safety demo path, while the high-detail maintenance route exposes a measured 48s prompt-stuffed slow path that we are replacing with Jetson-owned session evidence. The benchmark is intentionally visible: latency, request ids, output contracts, audit state, systemd status, model manifest, and token-budget tradeoffs are all documented.
```

Updated judge-facing version after real M400 testing:

```text
WearEdge Pro has moved from simulated images to real Vuzix M400 field capture. The fastest static Jetson patrol path completes image requests in about 3.9-5.8s after warmup, while the current high-detail M400 lao-shi-fu maintenance loop averages about 45.8s because it uses a 560/560 visual-token budget to read labels, HMI values, gauges, and records. The project records this honestly: latency, visual token budget, request ids, memory/power envelope, service state, audit traces, and every stability issue are preserved. Across May 18-20 we turned failures into fixes: no on-glasses typing, Vuzix voice phrases, stale-session recovery, preview accept/reject, one-question sensory capture, visible retry on connection reset, and full-screen final actions.
```
