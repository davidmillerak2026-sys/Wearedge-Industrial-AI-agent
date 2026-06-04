# Screenshots Checklist

更新日期：2026-06-04

| 截图 | 必需 | 状态 | 说明 |
| --- | --- | --- | --- |
| GitHub README 首页 | yes | pending | 展示赛事定位、Registration Fit、WFC endpoint。 |
| `python scripts/run_competition_eval.py` 输出 | yes | pending | 展示离线评估 summary。 |
| `docs/competition-offline-eval-report.md` 指标表 | yes | pending | 展示各赛事指标 PASS/REVIEW。 |
| `python scripts/smoke_workflow_canvas_decision.py` 输出 | yes | pending | 展示 primary direction、latency、function block count。 |
| `workflows/wearedge_wfc_poc_payload.json` | yes | pending | 展示 WFC 输入上下文。 |
| `/healthz` JSON | recommended | pending | 展示 gateway readiness 和 competition metadata。 |
| 工易魔方资源块截图 | when available | pending | 真实平台环境接入后补。 |
| 工易魔方 Python Function Block 截图 | when available | pending | 真实平台环境接入后补。 |
| Dashboard mock 截图 | yes | ready to capture | 使用 `docs/submission/dashboard-mock.html`，标注为 submission mock。 |
| 工易魔方 Dashboard 截图 | when available | pending | 真实平台环境接入后补。 |
| CI green run | recommended | pending | 展示 GitHub Actions 通过。 |

## 命名建议

将截图保存到外部提交素材目录，避免把大图直接放入 Git：

```text
submission-assets/screenshots/01-github-readme.png
submission-assets/screenshots/02-competition-eval-cli.png
submission-assets/screenshots/03-offline-eval-report.png
submission-assets/screenshots/04-wfc-smoke.png
submission-assets/screenshots/05-wfc-payload.png
```
