# First-Round Submission Attachment Index

更新日期：2026-06-12

用途：把报名系统最终上传、复制、截图、留档的材料按评审视角收敛到一页。此索引面向初赛提交，不替代 `docs/submission/final-action-board.md` 的缺口控制。

## Upload Priority

| Priority | Attachment | Source | Status | Use |
| --- | --- | --- | --- | --- |
| P0 | Business plan | `docs/submission/business-plan.md` | repo-ready draft | 初赛商业计划书主体，可转 DOCX/PDF/PPT。 |
| P0 | Technical solution | `docs/submission/technical-solution.md` | repo-ready draft | 技术方案主体，说明多智能体、端侧、Xcelerator/WFC 接入和安全边界。 |
| P0 | Repo-controlled submission bundle | `submission-assets/live-evidence/submission-bundle/wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip` | generated local asset | 一次性上传/留档的代码、文档、OpenAPI、WFC 原型、评估证据包。 |
| P0 | Demo video | `submission-assets/live-evidence/video/wearedge-enterprise-demo-3-5min.mp4` | generated local asset | 3-5 分钟演示视频；画面中已标注离线/平台 PoC/人工材料边界。 |
| P0 | Registration fields | `docs/submission/registration-fields.md` | ready | 报名系统文本字段复制源。 |
| P1 | Siemens co-creation one-pager | `docs/siemens-xcelerator-co-creation-onepager.md` | ready | 共创思路、目标客户、商业模式的短材料。 |
| P1 | Edge runtime evidence | `docs/finals-jetson-gateway-latency-benchmark-report.md` and `docs/submission/evidence/finals-jetson-gateway-latency-benchmark.json` | generated | 证明 Jetson 端侧 FastAPI HTTP 决策路径、300 iterations / 4500 samples、p95/max 延迟和资源 profile。 |
| P1 | Offline evaluation report | `docs/competition-offline-eval-report.md` | ready | 初赛“通过离线数据集验证”的指标表与边界说明。 |
| P1 | Finals foundation report | `docs/finals-validation-report.md` | generated | 决赛方向覆盖、>=90% 决策准确率、<=500ms 延迟基础。 |
| P1 | Xcelerator OpenAPI spec | `openapi/wearedge-xcelerator-apiworld.openapi.json` | ready | API World 导入/复现材料。 |
| P1 | Gongyi Mofang WFC resource package | `submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/wearedge-agent-service-0.1.0.zip` | generated local asset | 资源块原型包；不是 live WFC 成功运行证明。 |
| P2 | Final readiness report | `docs/submission/final-readiness-report.md` | generated | 内部总控状态，不一定上传给评委。 |
| P2 | Final action board | `docs/submission/final-action-board.md` | generated | 最后补证据/补人工文件的操作清单，不建议作为评审主附件。 |

## Screenshot And Live Evidence Pack

| Evidence area | Location | Current submit wording |
| --- | --- | --- |
| Xcelerator API World | `submission-assets/live-evidence/xcelerator/` | 可描述为真实平台草稿/导入证据；未发布上架。 |
| Gongyi Mofang project, Python block, data table | `submission-assets/live-evidence/gongyi-mofang/` | 可描述为真实 WFC 项目和配置证据。 |
| Gongyi Mofang Dashboard/run-log/HumanApprovalGate 04/05/06 | `submission-assets/live-evidence/gongyi-mofang/04-06*` | `04` Dashboard、`05` run-log `ok=true`、`06` HumanApprovalGate 均已作为 live WFC 证据保留；若界面变化需重新截图复核。 |
| Edge runtime | `submission-assets/live-evidence/edge-runtime/` | 可描述为 Jetson/端侧 FastAPI HTTP 决策路径证据；stdlib gateway 只作为 fallback 历史证据。 |
| Submission screenshots | `submission-assets/live-evidence/submission/` | 最终填报/提交成功后补齐。 |
| Legal/company files | `submission-assets/live-evidence/legal/` | 企业负责人补齐；不提交 Git。 |

## Suggested Upload Set

报名系统若附件数量有限，优先上传：

1. `business-plan.md` 转出的 PDF/DOCX。
2. `technical-solution.md` 转出的 PDF/DOCX。
3. `wearedge-industrial-ai-agent-repo-controlled-submission-bundle.zip`。
4. `wearedge-enterprise-demo-3-5min.mp4`。
5. `finals-jetson-gateway-latency-benchmark-report.md` 转 PDF，或与技术方案合并。
6. `competition-offline-eval-report.md` 转 PDF，或与技术方案合并。
7. 最终企业签字/盖章文件和报名系统截图。

如果附件数量更宽裕，再追加：

1. Xcelerator API World 截图包。
2. Gongyi Mofang WFC 截图包。
3. WFC resource package zip。
4. OpenAPI JSON。
5. Co-creation one-pager。

## Do Not Upload Publicly Without Review

- WFC password, session cookies, Xcelerator AppSecret, API tokens.
- AppID/AppSecret 完整截图。
- 统一社会信用代码、联系人手机号、邮箱等未脱敏截图。
- `submission-assets/live-evidence/legal/` 中的真实企业文件，除非只上传到官方报名系统。
- 任何 `.fallback.json` 仍存在的截图，不得改名或表述成 live WFC 成功运行。

## Claim Boundaries

可说：

- Wearedge 已具备可运行的端侧工业智能体 runtime，可在 Jetson/IPC/本地工控机形态部署。
- `/v1/workflow-canvas/decision` 已有离线评估、HTTP smoke、Jetson FastAPI 端侧 latency/resource 证据。
- Xcelerator API World 和 Gongyi Mofang WFC 已形成平台接入草稿、资源块、Python block、数据表和演示闭环基础。

不可说：

- 不把本地 mock 或 smoke test 截图说成 live 平台闭环；当前 `04/05/06` WFC 证据可按 live evidence manifest 的状态描述。
- 不说已经有真实客户生产数据或量产部署，除非后续有客户授权日志。
- 不说 Gemma 4 E2B 或任何基础模型是自研。
- 不说模型直接控制 PLC、机器人、停线、放行或能耗切换。

## Final Pre-Upload Commands

```powershell
python scripts/run_final_readiness_pipeline.py --json
python scripts/generate_final_action_board.py --write
python scripts/verify_submission_package.py --write-manifest
python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest
python scripts/verify_final_external_assets.py --allow-incomplete --write-report
python scripts/build_final_submission_bundle.py --json
```

Expected before final human files:

```text
repo_ready=True
foundation_ready=True
final_ready=False
missing=6
fallback_warnings=3
```

Expected after final human files and live WFC replacement:

```text
repo_ready=True
foundation_ready=True
final_ready=True
missing=0
fallback_warnings=0
```
