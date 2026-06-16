# Screenshots Checklist

更新日期：2026-06-16

| 截图 | 必需 | 状态 | 说明 |
| --- | --- | --- | --- |
| GitHub README / local README 首页 | yes | captured locally | `submission-assets/screenshots/01-local-readme.png`，展示赛事定位、Registration Fit、WFC endpoint。 |
| `python scripts/run_competition_eval.py` 输出 | yes | captured locally | `submission-assets/screenshots/02-competition-eval-cli.png`，展示离线评估 summary。 |
| `docs/competition-offline-eval-report.md` 指标表 | yes | captured locally | `submission-assets/screenshots/03-offline-eval-report.png`，展示各赛事指标 PASS/REVIEW。 |
| `python scripts/smoke_workflow_canvas_decision.py` 输出 | yes | captured locally | `submission-assets/screenshots/04-wfc-smoke.png`，展示 primary direction、latency、function block count。 |
| `workflows/wearedge_wfc_poc_payload.json` | yes | captured locally | `submission-assets/screenshots/05-wfc-payload.png`，展示 WFC 输入上下文。 |
| `/healthz` JSON | recommended | pending | 展示 gateway readiness 和 competition metadata。 |
| `/v1/edge/runtime-profile` JSON | yes | captured locally | `submission-assets/screenshots/12-edge-runtime-profile.png`，展示 Jetson/IPC/local server 端侧 Agent Runtime、WFC-ready 和安全边界。 |
| `/v1/industrial-agent/solution-profile` JSON | yes | pending | 展示工业问题、Gemma 4 E2B/llama.cpp 模型角色、KPI 决策矩阵、Agent 分工和 HumanApprovalGate。 |
| 稳定 HTTPS endpoint verifier | recommended | pending | 运行 `python scripts/verify_stable_wearedge_endpoint.py --base-url https://<stable-host> --write-evidence`，输出 `submission-assets/live-evidence/stable-endpoint/stable-endpoint-evidence.md`；临时 tunnel 不能写成稳定复现地址。 |
| WFC resource block prototype | yes | captured locally | `submission-assets/screenshots/13-wfc-resource-block-prototype.png`，展示 `deploymentMode` 和资源参数。 |
| Xcelerator API World 服务截图 | when available | pending | 保存到 `submission-assets/live-evidence/xcelerator/`，按 live evidence runbook 命名。 |
| 工易魔方项目/画布基础截图 | when available | captured live | 已保存 `submission-assets/live-evidence/gongyi-mofang/07-18*.png` 辅助截图，含项目创建、项目卡、编辑器、资源配置、工作流画布、编程库和右侧面板入口。 |
| 工易魔方资源块截图 | when available | partial | `01-resource-block-wearedge-agent-service.png` 已替换为真实 `Wearedge Agent Service` 自定义资源属性面板，并显示 `Agent Host` 参数；`agentPort`、`apiKeyRef`、`deploymentMode`、`plantId`、`lineId` 仍需补全。 |
| 工易魔方 Python Function Block 截图 | when available | captured | `02-python-function-block-call-api.png` 已显示主线 `CallWearedgeDecisionApi`、属性面板、输入/输出和异常处理；`103-wfc-python-fb-main-search-state.png` 已显示 live `fb_main.py` 中的 Wearedge 摘要字段。 |
| Dashboard mock 截图 | yes | captured locally | 使用 `docs/submission/dashboard-mock.html`，本地素材路径 `submission-assets/screenshots/06-dashboard-mock.png`。 |
| Finals HMI console 截图 | yes | captured locally | 使用 `docs/submission/finals-hmi-console.html`，本地素材路径 `submission-assets/screenshots/17-finals-hmi-console.png`，展示自然语言输入、决策路径、证据引用、审计轨迹和 HumanApprovalGate。 |
| 工易魔方数据表字段截图 | when available | captured | `03-global-data-table-decision-fields.png` 已在 live WFC `编辑数据表 -> 自定义数据` 中显示 8 个 Wearedge 决策字段；`110-wfc-data-table-fields-drawer-live-20260612.png` 作为同类早期 live 抽屉证据保留。 |
| 工易魔方 `更新数据表` 绑定截图 | when available | captured live | `129-wfc-update-data-table-field-options-20260612.png` 显示真实 WFC 字段下拉；`141-wfc-update-data-table-binding-confirmed-20260612.png` 显示 `更新数据表.1` 已绑定 `selected_direction`、`priority`、`recommended_action`、`approval_status`；`192-wfc-update-data-table-fields-complete-20260613.png` 显示四个字段已填入示例值；`193-wfc-debug-running-fields-locked-20260613.png` 显示 DEBUG 运行态下字段锁定。2026-06-16 live 调试确认 direct callback 可能卡住 DEBUG，因此最终写表路线应建立 `输出1 -> 更新数据表.1` 数据端口虚线。 |
| 工易魔方 Python 动态写回输出 | recommended | captured live | `196-wfc-dynamic-writeback-output-ok-20260616.png` 显示真实 WFC DEBUG 中 `CallWearedgeDecisionApi.output` 开头 `ok=true`、`状态码 Good`；同目录 `196-wfc-dynamic-output-ok-dom-20260616.json` 保存完整字段，包含 `wfc_writeback.method=wfc_output1_to_update_data_table` 和 `fields_ready`。 |
| 工易魔方数据表运行后动态值 | recommended | pending | 目标截图 `197-wfc-data-table-values-after-python-writeback-20260616.png`，应显示运行后数据表中的 `selected_direction`、`approval_status`、`recommended_action`、`latency_ms` 与 Python 输出 `fields_ready` 一致。 |
| 工易魔方 Dashboard 截图 | when available | captured live | `04-dashboard-decision-view.png` 已替换为 Wearedge WFC PoC / SiteScope live dashboard 展示图，包含指标卡、决策路径、HumanApprovalGate 和 workflow state；`71-wfc-dashboard-explorer-entry-native.png` 作为 Dashboard Explorer 入口辅助证据保留。 |
| 工易魔方原生运行状态截图 | when available | captured live | `124-wfc-debug-status-good-fullpage-20260612.png` 与 `125-wfc-run-log-workflow-ready-status-good-20260612.png` 已显示 DEBUG、SPIDR、`CallWearedgeDecisionApi` 和原生输出 `状态码 Good`；`05-run-log-ok-true.png` 已于 2026-06-13 替换为 live WFC 原生日志，显示 `CallWearedgeDecisionApi.output` JSON 开头 `"ok": true`；`196-wfc-dynamic-writeback-output-ok-20260616.png` 进一步显示新版 Function Block 输出 `ok=true` 和 `状态码 Good`，完整 DOM 证据包含 `wfc_writeback.method=wfc_output1_to_update_data_table`。 |
| 工易魔方运行日志截图 | when available | captured live | `05-run-log-ok-true.png` 显示 WFC 原生运行日志中的 `ok=true` 业务输出，配套 `05-run-log-ok-true.review.json`；`195-wfc-browser-debug-log-20260613.json` 保存浏览器运行期日志，包含 `makeWorkflowReadOnly`、`update workflow state` 和 `update data table`。最终增强目标是让原生数据表值直接显示 latency、selected direction 和 approval status。 |
| 工易魔方人工确认截图 | when available | captured live | `06-human-approval-gate.png` 已替换为 Wearedge WFC PoC / SiteScope live HumanApprovalGate 裁剪图，显示 `approval_status=pending_human_approval`、残余风险、证据和确认/驳回按钮；`192-wfc-update-data-table-fields-complete-20260613.png` 和 `193-wfc-debug-running-fields-locked-20260613.png` 作为数据表字段承载人工确认状态的辅助证据。 |
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
submission-assets/screenshots/17-finals-hmi-console.png
submission-assets/screenshots/07-api-schema.png
submission-assets/screenshots/08-submission-verifier.png
submission-assets/screenshots/09-pytest-output.png
submission-assets/screenshots/10-registration-fields.png
submission-assets/screenshots/11-co-creation-onepager.png
submission-assets/screenshots/12-edge-runtime-profile.png
submission-assets/screenshots/16-solution-profile.png
submission-assets/screenshots/13-wfc-resource-block-prototype.png
submission-assets/screenshots/14-enterprise-winning-strategy.png
submission-assets/screenshots/15-edge-runtime-doc.png
```

真实平台截图采集完成后运行：

```powershell
python scripts/verify_live_evidence.py --stage platform --write-manifest
```
