# Capture Runbook

更新日期：2026-06-04

目标：用当前仓库材料录制初赛截图和 3-5 分钟演示视频。若暂时没有真实工易魔方平台环境，先使用 API、离线评估、Dashboard mock 作为初版证据，并明确标注“模拟/离线验证”。

## 准备命令

```powershell
cd "C:\Users\ryan hui\Documents\Wearedge-Industrial AI agent"
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/run_competition_eval.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/smoke_workflow_canvas_decision.py
& "C:\tmp\wearedge-ci-venv\Scripts\python.exe" scripts/build_submission_evidence.py
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
| 8 | pytest output | terminal or CI |

## Dashboard Mock

Open this file in a browser:

```text
docs/submission/dashboard-mock.html
```

Suggested screenshot name:

```text
submission-assets/screenshots/06-dashboard-mock.png
```

## Video Flow

1. Start with the README and explain Siemens Xcelerator / Gongyi Mofang fit.
2. Show `workflows/wearedge_wfc_poc_payload.json` and explain data sources.
3. Run or show `scripts/smoke_workflow_canvas_decision.py` output.
4. Open `docs/submission/dashboard-mock.html` and explain decision visualization.
5. Open `docs/competition-offline-eval-report.md` and explain simulated/offline metric status.
6. Close with `docs/siemens-xcelerator-co-creation-onepager.md` and business model.

## Boundary Statement For Narration

Use this sentence in the video:

```text
当前指标来自仓库内模拟/离线数据集，用于初赛前工程验证；真实工易魔方/Xcelerator 平台截图和客户现场数据将在联合 PoC 阶段补齐。
```
