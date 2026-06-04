# Wearedge 赛事离线评估报告

生成日期：2026-06-04

## 结论

本报告基于 `evals/competition_offline_dataset.jsonl` 中的 5 条模拟/离线样例，调用 `jetson.competition.build_competition_decision()` 评估多智能体协同决策输出。

重要边界：这些结果用于初赛前的工程自测和指标对齐，**不是客户真实产线数据**；后续需要在工易魔方或西门子 Xcelerator PoC 环境中复现。

## 指标摘要

| 指标 | 离线结果 | 赛事目标 | 状态 |
| --- | --- | --- | --- |
| Decision case pass rate | 100.0% | >= 90% | PASS |
| Decision accuracy estimate | 95.0% min | >= 90.0% | PASS |
| Interactive latency | 1 ms max | <= 500 ms | PASS |
| Maintenance F1 | 87.0% min | >= 85.0% | PASS |
| Maintenance warning lead | 25.0 h min | >= 24.0 h | PASS |
| Root cause Top 3 | 91.0% min | >= 90.0% | PASS |
| Energy forecast accuracy | 95.5% min | >= 95.0% | PASS |
| Energy saving estimate | 10.5% min | >= 10.0% | PASS |
| Quality relative improvement | 5.5% min | >= 5.0% | PASS |
| Schedule efficiency gain | 21.0% min | >= 20.0% | PASS |

## 样例结果

| Case | Primary Direction | Direction Count | Accuracy Estimate | Latency | Human Confirmation | Result |
| --- | --- | ---: | ---: | ---: | --- | --- |
| pkg_line_joint_high_maintenance | maintenance | 5 | 97.0% | 1 ms | True | PASS |
| iqc_defect_containment | quality | 4 | 96.5% | 1 ms | True | PASS |
| energy_peak_optimization | energy | 4 | 96.5% | 1 ms | True | PASS |
| flexible_changeover_joint | flexible_production | 4 | 96.5% | 1 ms | True | PASS |
| workflow_canvas_resource_binding | workflow_canvas | 3 | 95.0% | 1 ms | True | PASS |

## 数据来源与下一步

- 当前样例来自本仓库内的模拟 MES、质量、能源、维护和 Workflow Canvas 上下文表。
- 下一步需要把同样 schema 接入工易魔方全局数据表、Dashboard 和真实或仿真的 SPIDR/IPC 运行日志。
- 报名材料中引用本报告时，应写作“离线模拟验证”，不要写成“客户现场生产验证”。
