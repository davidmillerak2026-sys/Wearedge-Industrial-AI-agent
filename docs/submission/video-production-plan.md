# Demo Video Production Plan

更新日期：2026-06-09

目标：制作一条 3-5 分钟企业组演示视频，让评委在短时间内看到 Wearedge 的差异化：智能体运行在端侧算力，Xcelerator / 工易魔方负责编排、审批和回写。

## 视频结构

| 时间 | 画面 | 口播重点 | 证据来源 |
| --- | --- | --- | --- |
| 0:00-0:20 | 项目标题、README、企业组定位 | Wearedge 是企业可交付的工业智能体联合解决方案，不是工业问答 demo。 | `README.md` |
| 0:20-0:55 | Edge runtime profile、健康检查、本地终端 | 智能体可部署在 Jetson / IPC / 本地工控机 / 边缘服务器，数据可留在产线侧。 | `edge-runtime/01-healthz.png`、`edge-runtime/02-runtime-profile.png` |
| 0:55-1:35 | Xcelerator / API World 服务页 | 平台可识别 Wearedge API，接口包括 WFC decision 和 edge runtime profile。 | `xcelerator/*.png` |
| 1:35-2:25 | 工易魔方资源块、Python Function Block、数据表 | 工易魔方把端侧 Agent Service 编排进工作流，并把输出写入数据表。 | `gongyi-mofang/*.png` |
| 2:25-3:10 | 决策输出、Dashboard、HumanApprovalGate | 多智能体协同输出主方向、建议动作、指标和人工确认项，高风险动作不直接控制 OT。 | Dashboard / WFC run log |
| 3:10-3:45 | 离线评估指标表、pytest、smoke test | 工程证据可复验，离线指标标注清楚，不夸大为客户真实数据。 | `docs/competition-offline-eval-report.md`、测试截图 |
| 3:45-4:30 | 商业计划、目标客户、ROI | 面向汽车零部件、电子装配、包装/食品/医药等换型频繁产线，与西门子共创行业模板。 | `docs/submission/business-plan.md` |
| 4:30-5:00 | 收尾页、提交材料索引 | 强调端侧可部署、平台可共创、产线可落地。 | `docs/submission/poc-evidence-index.md` |

## 必须出现的字幕标签

- `离线/模拟验证`：用于离线评估、mock dashboard、本地 smoke test。
- `真实平台截图`：用于 Xcelerator / 工易魔方账号环境画面。
- `端侧运行证据`：用于 Jetson / IPC / 本地边缘节点画面。
- `人工确认边界`：用于 HumanApprovalGate 或安全边界画面。

## 录屏顺序

1. 打开本地服务或展示 `/healthz`。
2. 运行 `python scripts/smoke_edge_runtime_profile.py`。
3. 展示 Xcelerator / API World 导入或服务详情截图。
4. 展示工易魔方资源块和 Function Block 截图。
5. 运行 `python scripts/smoke_workflow_canvas_decision.py` 或展示平台运行日志。
6. 展示 Dashboard / 数据表 / HumanApprovalGate。
7. 展示 `python scripts/run_competition_eval.py` 和 pytest 结果。
8. 展示商业计划和共创 one-pager。

## A/B 路径

| 路径 | 使用条件 | 视频口径 |
| --- | --- | --- |
| A 路：真实平台版 | Xcelerator / 工易魔方环境可登录且能截图 | “已完成平台 PoC 接入路径验证。” |
| B 路：本地备用版 | 平台环境临时不可用或网络不稳定 | “当前使用本地 API、资源块原型和 Dashboard mock 展示闭环，真实平台截图将在联合 PoC 环境复现。” |

## 最终文件

保存到忽略目录：

```text
submission-assets/live-evidence/video/wearedge-enterprise-demo-3-5min.mp4
submission-assets/live-evidence/video/wearedge-enterprise-demo-script-final.md
```

最终视频不要超过 5 分钟；初赛材料中优先使用 3-4 分钟版本，答辩备用可保留更长录屏。
