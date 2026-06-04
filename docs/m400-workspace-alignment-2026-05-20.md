# M400 Workspace Alignment Snapshot

Date: 2026-05-20 CST

Purpose: align the current Windows workspace after the M400 wearable field-test cycle, without deleting evidence or reverting local work.

## Current Product Baseline

- Android app baseline: `0.3.18-m400-a11-final-actions`
- Installed package observed on M400: `versionCode=20`, `versionName=0.3.18-m400-a11-final-actions`
- APK path: `clients/m400/android/app/build/outputs/apk/debug/app-debug.apk`
- APK repository status: local generated artifact, ignored by `clients/m400/android/.gitignore` through `build/`, not tracked by Git.
- Main behavior under test: manual WearEdge launch, `capture photo -> preview -> accept -> Jetson`, multi-evidence Lao-Shi-Fu agent loop, operator sensory one-question-at-a-time, final full-screen conclusion, simulated follow-up action confirmations.

## Code Files In Scope

These files form the current M400 app implementation and should be kept together when committing the M400 client update:

- `clients/m400/android/app/build.gradle.kts`
- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/MainActivity.kt`
- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/WearEdgeVoiceAdapter.kt`
- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/CaptureConfirmation.kt`
- `clients/m400/android/app/src/main/java/com/wearedge/m400demo/PhotoConfirmationGate.kt`
- `clients/m400/android/README.md`

`CaptureConfirmation.kt`, `PhotoConfirmationGate.kt`, this playbook, and this alignment snapshot are currently new files in the Windows workspace and need to be explicitly staged when committing the M400 update.

## Documentation Aligned In This Pass

- `docs/m400-field-test-learnings.md`: adds Learning 23 for final conclusion, simulated follow-up actions, speech interruption, and visible connection-reset recovery.
- `docs/m400-lao-shi-fu-field-test-playbook.md`: updates the field-test path to current `capture photo -> preview -> accept` behavior, final analyzing, and full-screen final action confirmation.
- `docs/test-log-history.md`: records the 2026-05-20 `0.3.18` build/install and workspace alignment result.

## Evidence Snapshot

Primary worn-test evidence is under:

```text
docs/poc-results/m400-worn-comparison-20260520-181119/
```

Important files:

- `m400-log-crawl-report-20260520-181119.md`
- `field-test-summary-20260520-181119.md`
- `m400-full-log-index-20260520-181119.md`
- `voice-dialogue-timeline-20260520-181119.log`
- `camera-upload-timeline-20260520-181119.log`
- `jetson-agent-response-extract-20260520-181119.log`
- `ui-visible-text-timeline-20260520-181119.md`
- `logcat.txt`
- `screen-*.png`
- `window-*.xml`

These are evidence artifacts, not source code. Keep them for product proof and later documentation, but stage them intentionally because the logcat and screenshots can be large.

## Adjacent Work Not Part Of The M400 App Commit

The following files appear to belong to competition/submission packaging or separate collateral. They should be reviewed as a separate commit scope:

- `docs/competition-registration-2026.md`
- `docs/submissions/`
- `scripts/generate_sziedc_submission_video.py`

## Do Not Delete

No cleanup was performed in this pass. The workspace contains field evidence, generated logs, Android build output, and submission materials. Treat untracked files as potentially meaningful until each one is reviewed.

## Next Commit Boundary

Recommended M400 commit scope:

1. Android app source and README for `0.3.18-m400-a11-final-actions`.
2. M400 learnings and playbook updates.
3. This workspace alignment snapshot.
4. Selected M400 field evidence files from `docs/poc-results/m400-worn-comparison-20260520-181119/` if the commit is intended to preserve proof artifacts.

Recommended separate commit scope:

1. Competition registration/submission documents.
2. Generated submission video scripts and assets.
