# Live Platform Evidence Runbook

更新日期：2026-06-09

目标：把真实 Xcelerator / 工易魔方平台证据采集成一套可复核素材，支撑企业组“端侧智能体 + 平台编排 + 人工确认 + 数据回写”的夺冠叙事。

重要边界：

- 不在 Git 仓库中保存平台账号、密码、token、企业证件号码截图或客户敏感数据。
- 真实截图、签署文件和视频放入 `submission-assets/live-evidence/`，该目录已被 `.gitignore` 忽略。
- 如果平台环境暂时不可用，用本地 API、WFC 原型包和 Dashboard mock 作为备用证据，并在材料中标注“待平台复现”。

## 初始化素材目录

```powershell
cd "C:\Users\ryan hui\Documents\Wearedge-Industrial AI agent"
python scripts/verify_live_evidence.py --init --allow-missing --write-manifest
```

生成目录：

```text
submission-assets/live-evidence/
  xcelerator/
  gongyi-mofang/
  edge-runtime/
  video/
  legal/
  submission/
```

## Xcelerator / API World 截图

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `xcelerator/01-tenant-or-workspace.png` | 租户、工作台或服务空间页面 | 证明账号和平台空间已具备接入入口；遮挡个人邮箱和敏感 ID。 |
| `xcelerator/02-apiworld-openapi-import.png` | API World OpenAPI 导入或服务创建页面 | 展示 `openapi/wearedge-xcelerator-apiworld.openapi.json` 可作为平台服务描述。 |
| `xcelerator/03-apiworld-service-detail.png` | Wearedge API 服务详情 | 展示服务名、接口列表、`/v1/workflow-canvas/decision`、`/v1/edge/runtime-profile`。 |
| `xcelerator/04-runtime-profile-api-test.png` | 平台 API 测试或调用结果 | 展示 `ok=true`、`workflow_canvas_ready=true`、`model_direct_ot_control=false`。 |

## 工易魔方 / Workflow Canvas 截图

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `gongyi-mofang/01-resource-block-wearedge-agent-service.png` | `Wearedge Agent Service` 资源块配置 | 参数至少包含 `agentHost`、`agentPort`、`apiKeyRef`、`deploymentMode`、`plantId`、`lineId`。 |
| `gongyi-mofang/02-python-function-block-call-api.png` | Python Function Block 编辑页 | 展示 `CallWearedgeDecisionApi` 调用 `/v1/workflow-canvas/decision`。 |
| `gongyi-mofang/03-global-data-table-decision-fields.png` | 全局数据表字段 | 展示主方向、优先级、建议动作、证据、指标、责任人、残余风险、人工确认状态。 |
| `gongyi-mofang/04-dashboard-decision-view.png` | Dashboard | 展示指标卡、决策路径、确认项、工作流状态。 |
| `gongyi-mofang/05-run-log-ok-true.png` | 运行日志 | 展示 `ok=true`、function blocks、latency 或成功写表记录。 |
| `gongyi-mofang/06-human-approval-gate.png` | 人工确认节点 | 证明高风险动作不会由模型直接控制 OT。 |

## 端侧运行证据截图

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `edge-runtime/01-healthz.png` | `/healthz` 或服务启动终端 | 证明 Wearedge Agent Service 已运行。 |
| `edge-runtime/02-runtime-profile.png` | `/v1/edge/runtime-profile` 输出 | 展示 Jetson / IPC / local server 部署能力和安全边界。 |
| `edge-runtime/03-workflow-canvas-decision-smoke.png` | `scripts/smoke_workflow_canvas_decision.py` 输出 | 证明 WFC decision API 可跑通。 |
| `edge-runtime/04-jetson-ipc-local-node.png` | Jetson、IPC、本地工控机或边缘服务器画面 | 证明智能体运行时可放在端侧算力中；如果硬件未到位，用本地工控机/边缘服务器证据替代。 |

## 企业与合规材料

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `legal/company-info-filled.md` | 企业主体、联系人、团队分工最终版 | 不提交到 Git；用于报名系统复制和内部核对。 |
| `legal/ip-and-no-dispute-signed.pdf` | 知识产权和无产权纠纷承诺 | 需企业负责人签字或盖章。 |
| `legal/no-adverse-record-signed.pdf` | 无不良记录承诺 | 需企业负责人签字或盖章。 |
| `legal/submission-contact-confirmation.md` | 报名联系人确认 | 包含联系人、电话、邮箱、备用联系人。 |

## 演示视频材料

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `video/wearedge-enterprise-demo-3-5min.mp4` | 最终演示视频 | 3-5 分钟，包含端侧运行、平台编排、人工确认、商业价值。 |
| `video/wearedge-enterprise-demo-script-final.md` | 最终口播稿 | 与视频一致，明确离线/真实平台边界。 |

## 报名系统截图

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `submission/01-registration-form-filled.png` | 报名系统字段已填 | 截图前遮挡敏感证件号码。 |
| `submission/02-submission-success.png` | 提交成功状态 | 作为 2026-07-08 内部提交目标的最终证据。 |

## 校验命令

平台证据阶段：

```powershell
python scripts/verify_live_evidence.py --stage platform --write-manifest
```

最终提交阶段：

```powershell
python scripts/verify_live_evidence.py --stage final --write-manifest
```

如果只是想查看缺口、不希望命令失败：

```powershell
python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest
```

## 口播边界

建议在视频和答辩中固定使用：

```text
Wearedge 当前仓库证据包含离线模拟验证和平台接入 PoC。真实 Xcelerator / 工易魔方截图用于证明平台接入路径；客户真实产线数据和量产效果将在后续联合 PoC 阶段补充，不在初赛阶段夸大为已量产。
```
