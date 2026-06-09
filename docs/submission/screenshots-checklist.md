# Screenshots Checklist

更新日期：2026-06-09

| 截图 | 必需 | 状态 | 说明 |
| --- | --- | --- | --- |
| GitHub README / local README 首页 | yes | captured locally | `submission-assets/screenshots/01-local-readme.png`，展示赛事定位、Registration Fit、WFC endpoint。 |
| `python scripts/run_competition_eval.py` 输出 | yes | captured locally | `submission-assets/screenshots/02-competition-eval-cli.png`，展示离线评估 summary。 |
| `docs/competition-offline-eval-report.md` 指标表 | yes | captured locally | `submission-assets/screenshots/03-offline-eval-report.png`，展示各赛事指标 PASS/REVIEW。 |
| `python scripts/smoke_workflow_canvas_decision.py` 输出 | yes | captured locally | `submission-assets/screenshots/04-wfc-smoke.png`，展示 primary direction、latency、function block count。 |
| `workflows/wearedge_wfc_poc_payload.json` | yes | captured locally | `submission-assets/screenshots/05-wfc-payload.png`，展示 WFC 输入上下文。 |
| `/healthz` JSON | recommended | pending | 展示 gateway readiness 和 competition metadata。 |
| `/v1/edge/runtime-profile` JSON | yes | captured locally | `submission-assets/screenshots/12-edge-runtime-profile.png`，展示 Jetson/IPC/local server 端侧 Agent Runtime、WFC-ready 和安全边界。 |
| WFC resource block prototype | yes | captured locally | `submission-assets/screenshots/13-wfc-resource-block-prototype.png`，展示 `deploymentMode` 和资源参数。 |
| Xcelerator API World 服务截图 | when available | pending | 保存到 `submission-assets/live-evidence/xcelerator/`，按 live evidence runbook 命名。 |
| 工易魔方项目/画布基础截图 | when available | captured live | 已保存 `submission-assets/live-evidence/gongyi-mofang/07-18*.png` 辅助截图，含项目创建、项目卡、编辑器、资源配置、工作流画布、编程库和右侧面板入口。 |
| 工易魔方资源块截图 | when available | partial | `01-resource-block-wearedge-agent-service.png` 已替换为真实 `Wearedge Agent Service` 自定义资源属性面板，并显示 `Agent Host` 参数；仍需补全其余参数。 |
| 工易魔方 Python Function Block 截图 | when available | pending | 保存到 `submission-assets/live-evidence/gongyi-mofang/02-python-function-block-call-api.png`；按文档从 `编程语言` 拖入 Python 程序块。 |
| Dashboard mock 截图 | yes | captured locally | 使用 `docs/submission/dashboard-mock.html`，本地素材路径 `submission-assets/screenshots/06-dashboard-mock.png`。 |
| 工易魔方 Dashboard 截图 | when available | pending | 保存到 `submission-assets/live-evidence/gongyi-mofang/04-dashboard-decision-view.png`。 |
| API schema | yes | captured locally | `submission-assets/screenshots/07-api-schema.png`，展示工易魔方 Python Function Block 调用方式。 |
| Submission verifier | yes | captured locally | `submission-assets/screenshots/08-submission-verifier.png`，展示仓库侧 ready。 |
| pytest output | yes | captured locally | `submission-assets/screenshots/09-pytest-output.png`，展示完整测试通过。 |
| Registration fields | recommended | captured locally | `submission-assets/screenshots/10-registration-fields.png`，展示报名字段短/中/长版本。 |
| Co-creation one-pager | yes | captured locally | `submission-assets/screenshots/11-co-creation-onepager.png`，展示共创思路、客户和商业模式。 |
| Enterprise winning strategy | recommended | captured locally | `submission-assets/screenshots/14-enterprise-winning-strategy.png`，展示企业组评分反推和端侧差异化。 |
| Edge runtime doc | recommended | captured locally | `submission-assets/screenshots/15-edge-runtime-doc.png`，展示端侧智能体运行时、部署模式和企业组金句。 |
| CI green run | recommended | pending | 展示 GitHub Actions 通过；若 CI 暂未开通，用本地 pytest 截图替代。 |

## 命名建议

将截图保存到外部提交素材目录，避免把大图直接放入 Git：

```text
submission-assets/screenshots/01-github-readme.png
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

真实平台截图采集完成后运行：

```powershell
python scripts/verify_live_evidence.py --stage platform --write-manifest
```
