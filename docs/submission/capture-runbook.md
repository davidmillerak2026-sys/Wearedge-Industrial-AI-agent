# Capture Runbook

更新日期：2026-06-09

目标：用当前仓库材料录制初赛截图和 3-5 分钟演示视频。若暂时没有真实工易魔方平台环境，先使用端侧 runtime profile、API、离线评估、WFC 资源块原型和 Dashboard mock 作为初版证据，并明确标注“模拟/离线验证”。

## 准备命令

```powershell
cd "C:\Users\ryan hui\Documents\Wearedge-Industrial AI agent"
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/run_competition_eval.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/smoke_workflow_canvas_decision.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/smoke_edge_runtime_profile.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/build_submission_evidence.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/verify_submission_package.py --write-manifest
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/capture_submission_screenshots.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" -m pytest --basetemp "C:\tmp\wearedge-industrial-ai-agent-pytest" tests industrial-rag-agent/tests
```

## 截图顺序

| Order | Screen | Source |
| --- | --- | --- |
| 1 | GitHub README / local README | `README.md` |
| 2 | Offline eval command output | terminal |
| 3 | Offline eval report metric table | `docs/competition-offline-eval-report.md` |
| 4 | WFC smoke command output | terminal |
| 5 | Workflow Canvas payload | `workflows/wearedge_wfc_poc_payload.json` |
| 6 | Dashboard mock | `docs/submission/dashboard-mock.html` |
| 7 | API schema | `docs/workflow-canvas-api-schema.md` |
| 8 | Submission verifier | terminal |
| 9 | pytest output | terminal or CI |
| 10 | Registration fields | `docs/submission/registration-fields.md` |
| 11 | Co-creation one-pager | `docs/siemens-xcelerator-co-creation-onepager.md` |
| 12 | Edge runtime profile smoke | terminal |
| 13 | WFC resource block prototype | `wfc-blocks/wearedge-agent-service/info.json` |
| 14 | Enterprise winning strategy | `docs/submission/enterprise-winning-strategy.md` |
| 15 | Edge runtime doc | `docs/edge-agent-runtime-for-xcelerator.md` |

## Dashboard Mock

Open this file in a browser:

```text
docs/submission/dashboard-mock.html
```

Suggested screenshot name:

```text
submission-assets/screenshots/06-dashboard-mock.png
```

Automated capture command:

```powershell
python scripts/capture_submission_screenshots.py
```

Generated local paths:

```text
submission-assets/screenshots/01-local-readme.png
submission-assets/screenshots/02-competition-eval-cli.png
submission-assets/screenshots/03-offline-eval-report.png
submission-assets/screenshots/04-wfc-smoke.png
submission-assets/screenshots/05-wfc-payload.png
submission-assets/screenshots/06-dashboard-mock.png
submission-assets/screenshots/07-api-schema.png
submission-assets/screenshots/08-submission-verifier.png
submission-assets/screenshots/09-pytest-output.png
submission-assets/screenshots/10-registration-fields.png
submission-assets/screenshots/11-co-creation-onepager.png
submission-assets/screenshots/12-edge-runtime-profile.png
submission-assets/screenshots/13-wfc-resource-block-prototype.png
submission-assets/screenshots/14-enterprise-winning-strategy.png
submission-assets/screenshots/15-edge-runtime-doc.png
```

## Video Flow

1. Start with the README and explain enterprise-group fit.
2. Run or show `scripts/smoke_edge_runtime_profile.py` to prove edge Agent Runtime readiness.
3. Show `wfc-blocks/wearedge-agent-service/info.json` and explain deployment mode parameters.
4. Show `workflows/wearedge_wfc_poc_payload.json` and explain data sources.
5. Run or show `scripts/smoke_workflow_canvas_decision.py` output.
6. Open `docs/submission/dashboard-mock.html` and explain decision visualization.
7. Open `docs/competition-offline-eval-report.md` and explain simulated/offline metric status.
8. Close with `docs/siemens-xcelerator-co-creation-onepager.md` and business model.

## Boundary Statement For Narration

Use this sentence in the video:

```text
当前指标来自仓库内模拟/离线数据集，用于初赛前工程验证；真实工易魔方/Xcelerator 平台截图和客户现场数据将在联合 PoC 阶段补齐。
```
