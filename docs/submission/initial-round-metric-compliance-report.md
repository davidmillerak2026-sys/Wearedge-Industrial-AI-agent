# Wearedge 初赛指标符合性汇总报告

更新日期：2026-06-15

## 1. 结论

按赛事初赛指标核对，Wearedge 当前已具备可提交的技术证据链：

| 初赛要求 | 当前状态 | 关键证据 |
| --- | --- | --- |
| 完成单智能体核心功能开发，故障预测准确率 >=85%，或调度优化效率提升 >=20% | 已满足，而且两条能力均有离线指标 | 设备运维维护 F1 最低 87.0%；柔性生产调度效率提升最低 21.0% |
| 提交技术方案文档与算法原型代码，或提交可执行的工易魔方工作流 | 已满足 | 技术方案、核心算法代码、Workflow Canvas 接入包、WFC live 截图与运行日志均已形成 |
| 通过离线数据集验证 | 已满足 | 5 条初赛离线样例全部通过，case pass rate 100.0%，目标检查全部通过 |

边界说明：上述结果来自项目自建离线/仿真数据集和平台 PoC 证据，不表述为真实客户生产数据，也不表述为已量产结果。高风险动作均进入 `HumanApprovalGate`，不由模型直接控制 PLC、质量放行或能源策略下发。

## 2. 单智能体核心功能开发

初赛要求允许以“故障预测准确率 >=85%”或“调度优化效率提升 >=20%”作为核心功能达标项。当前项目同时保留两条可提交口径。

| 能力项 | 当前实现 | 离线验证结果 | 是否达标 |
| --- | --- | ---: | --- |
| 设备运维智能体：故障预测/预警 | `jetson.competition.build_competition_decision()` 对维护上下文进行方向识别、风险评级、根因建议和人工确认判定 | 维护 F1 最低 87.0%，预警提前时间最低 25.0 小时，根因 Top3 最低 91.0% | 达标 |
| 柔性生产智能体：调度优化 | 在换型、订单变化、设备/质量/能耗约束下输出协同调度建议 | 调度效率提升最低 21.0%，平均 22.333%，最高 24.0% | 达标 |

提交口径建议：

- 主口径：设备运维智能体已完成核心功能开发，离线维护 F1 为 87.0%，满足故障预测准确率/预警判定质量 >=85% 的初赛要求。
- 备选/加强口径：柔性生产调度智能体离线效率提升最低 21.0%，同时满足调度优化效率提升 >=20% 的初赛要求。

## 3. 离线数据集来源与验证方法

离线数据集文件：

- `evals/competition_offline_dataset.jsonl`

数据来源与构造方式：

- 数据集为项目自建的离线/仿真验证集，不含真实客户生产数据。
- 样例覆盖设备运维、质量管控、能源管理、柔性生产、Workflow Canvas 平台接入五个方向。
- 每条样例包含 `selected_directions`、`context`、期望主方向、期望状态、期望是否需要人工确认等字段。
- 上下文模拟来自 MES、QMS、EMS、CMMS、设备运行、质量异常、能耗峰值、换型约束和 Workflow Canvas 资源绑定场景。

验证命令：

```powershell
python scripts/run_competition_eval.py
```

验证脚本调用：

- `scripts/run_competition_eval.py`
- `jetson.competition.build_competition_decision()`

本次复核结果：

```text
cases=5
passed=5
case_pass_rate_pct=100.0
decision_accuracy_pct_min=95.0
latency_ms_max=1
all_target_checks_passed=True
```

核心指标表：

| 指标 | 当前离线结果 | 目标 | 状态 |
| --- | ---: | ---: | --- |
| 离线样例通过率 | 100.0% | 完整通过 | 达标 |
| 决策准确率估算，最低值 | 95.0% | >=90% | 达标 |
| 规则决策延迟，最大值 | 1 ms | <=500 ms | 达标 |
| 维护 F1，最低值 | 87.0% | >=85% | 达标 |
| 根因 Top3，最低值 | 91.0% | >=90% | 达标 |
| 预警提前时间，最低值 | 25.0 h | >=24 h | 达标 |
| 调度效率提升，最低值 | 21.0% | >=20% | 达标 |
| 能源预测准确率，最低值 | 95.5% | >=95% | 达标 |
| 节能率估算，最低值 | 10.5% | >=10% | 达标 |
| 质量改善估算，最低值 | 5.5% | >=5% | 达标 |

详细报告与机器可读摘要：

- `docs/competition-offline-eval-report.md`
- `docs/submission/evidence/competition-eval-summary.json`

## 4. 技术方案文档与算法原型代码

可提交技术方案文档：

- `docs/submission/technical-solution.md`
- `docs/workflow-canvas-poc-runbook.md`
- `docs/workflow-canvas-api-schema.md`
- `docs/submission/business-plan.md`
- `docs/submission/judging-scorecard-evidence-map.md`

算法原型代码：

- `jetson/competition.py`：赛事方向评分、协同决策、指标估算、人工确认判定。
- `jetson/app.py`：FastAPI 网关，提供 `/v1/workflow-canvas/decision`、`/v1/infer`、`/v1/edge/runtime-profile`、`/healthz`。
- `scripts/run_competition_eval.py`：离线评估脚本。
- `tests/test_competition_eval.py`：竞赛评估回归测试。
- `scripts/smoke_workflow_canvas_decision.py`：Workflow Canvas decision API smoke test。

当前决策机制：

- 赛事指标验证和 WFC 协同决策由确定性决策器完成，保证结构化输出、可复验和可审计。
- 端侧推理 PoC 接入 Gemma 4 E2B，运行在 Jetson / IPC / 本地工控机路线中，用于自然语言、知识问答和辅助解释。
- 高风险动作进入 HumanApprovalGate，模型文本不直接下发 OT 控制。

## 5. 可执行工易魔方工作流证据

当前项目已形成可复现的工易魔方接入包：

- `wfc-blocks/wearedge-agent-service/`：`Wearedge Agent Service` 资源块原型。
- `workflows/wfc_call_wearedge_decision_fb_main.py`：`CallWearedgeDecisionApi` Python Function Block 示例。
- `workflows/wearedge_wfc_poc_payload.json`：WFC PoC 请求样例。
- `docs/workflow-canvas-poc-runbook.md`：从资源块、Function Block、全局数据表、Dashboard 到 HumanApprovalGate 的执行说明。

真实平台/截图证据：

- `submission-assets/live-evidence/live-evidence-manifest.md`：平台证据 25/25 present，ready=True。
- `submission-assets/live-evidence/gongyi-mofang/04-dashboard-decision-view.png`：工易魔方 Dashboard 决策视图。
- `submission-assets/live-evidence/gongyi-mofang/05-run-log-ok-true.png`：运行日志 `ok=true` 证据。
- `submission-assets/live-evidence/gongyi-mofang/06-human-approval-gate.png`：人工确认门证据。

平台证据复核命令：

```powershell
python scripts/verify_live_evidence.py --stage platform --write-manifest
```

本次复核结果：

```text
stage=platform
ready=True
present_count=25
missing_count=0
```

## 6. 初赛提交建议

初赛材料中建议这样表达：

> Wearedge 已完成面向设备运维和柔性生产场景的工业智能体核心功能开发。离线验证中，设备运维智能体维护 F1 最低 87.0%，满足故障预测准确率/预警判定质量 >=85% 的要求；柔性生产调度效率提升最低 21.0%，同时满足调度优化效率提升 >=20% 的要求。项目已提交技术方案文档、算法原型代码、Workflow Canvas 接入包，并通过自建离线数据集完成验证。当前验证数据为离线/仿真数据，后续 PoC 将在 Xcelerator / 工易魔方和真实产线环境中继续复验。

