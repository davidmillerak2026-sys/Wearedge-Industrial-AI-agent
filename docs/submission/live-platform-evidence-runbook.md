# Live Platform Evidence Runbook

更新日期：2026-06-12

目标：把真实 Xcelerator / 工易魔方平台证据采集成一套可复核素材，支撑企业组“端侧智能体 + 平台编排 + 人工确认 + 数据回写”的夺冠叙事。

重要边界：

- 不在 Git 仓库中保存平台账号、密码、token、企业证件号码截图或客户敏感数据。
- 真实截图、签署文件和视频放入 `submission-assets/live-evidence/`，该目录已被 `.gitignore` 忽略。
- 如果平台环境暂时不可用，用本地 API、WFC 原型包和 Dashboard mock 作为备用证据，并在材料中标注“待平台复现”。
- 官方资料到可执行路径的决策表见 `docs/gongyi-mofang-official-completion-paths.md`：GUI 仍是 live WFC 证据主路径；CLI/API 只用于资源包打包、只读探测、备份、smoke test 和本地证据生成。

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
| `xcelerator/05-app-group-created.png` | Wearedge 应用分组 | 展示自有应用分组和 `注册应用` 入口。 |
| `xcelerator/07-app-detail-created-redacted-top.png` | Wearedge 应用草稿 | 展示应用草稿存在；截图需避开 AppID / AppSecret 区域。 |
| `xcelerator/10-openapi-json-import-filled.png` | OpenAPI JSON/YAML 导入 | 展示 `openapi/wearedge-xcelerator-apiworld.openapi.json` 已填入平台导入框。 |
| `xcelerator/11-openapi-parse-preview.png` | OpenAPI 解析预览 | 新版应展示 `/healthz`、`/v1/edge/runtime-profile`、`/v1/industrial-agent/solution-profile`、`/v1/workflow-canvas/decision`。 |
| `xcelerator/13-openapi-three-apis-imported.png` | 历史 API 接口导入结果 | 2026-06-09 截图显示 3 个接口，保留为操作轨迹。 |
| `xcelerator/16-openapi-four-apis-imported.png` | 新版 API 接口导入结果 | 2026-06-11 已补充，展示服务接口列表含 4 个接口，新增 solution profile。 |
| `xcelerator/15-api-service-saved-unpublished-list.png` | Wearedge API 服务列表 | 展示服务名、`未发布` 状态、接口数 `4`、可见范围 `租户内`。 |
| `xcelerator/04-runtime-profile-api-test.png` | 平台 API 测试或调用结果 | 展示 `ok=true`、`workflow_canvas_ready=true`、`model_direct_ot_control=false`。 |
| `xcelerator/05-xcelerator-app-home-wearedge-drafts.png` | 应用主页复核 | 展示 `Wearedge 工业智能体 PoC` 分组和 `Wearedge 工业智能体服务` 应用卡片。 |
| `xcelerator/06-xcelerator-api-detail-basic-info-unpublished.png` | API 服务基础信息复核 | 展示服务名、服务版本、`未发布`、所属应用和 `租户内` 可见范围。 |
| `xcelerator/07-xcelerator-api-interface-list-four-endpoints-unpublished.png` | API 服务接口信息复核 | 展示 4 个未发布草稿接口：`/healthz`、`/v1/edge/runtime-profile`、`/v1/industrial-agent/solution-profile`、`/v1/workflow-canvas/decision`。 |
| `xcelerator/38-xcelerator-client-app-home-current.png` | 当前应用主页复核 | 最新截图，展示应用分组、应用卡片和租户内标识。 |
| `xcelerator/39-xcelerator-api-detail-current-draft.png` | 当前 API 详情草稿复核 | 最新截图，展示 `未发布`、所属应用、可见范围 `租户内`、服务器地址和 `/v1` 路径。 |
| `xcelerator/40-xcelerator-api-interface-list-current-four-endpoints.png` | 当前接口列表复核 | 最新截图，展示 4 个接口均为租户内、未启用草稿接口。 |

边界说明：

- `04-runtime-profile-api-test.png/json` 是临时 HTTPS PoC 网关的外部可达验证，不等同于 Xcelerator 已发布代理调用。
- `06/07-xcelerator-*` 和 `38/39/40-xcelerator-*` 截图证明 Xcelerator 草稿内的应用、API 服务和接口定义已经配置，但服务仍保持 `未发布` 和 `租户内`。

## 工易魔方 / Workflow Canvas 截图

文档确认的执行顺序：

1. 在项目页创建或打开 `Wearedge WFC PoC`。
2. 进入工作流编辑器，确认默认 `工作流.1` 可见。
3. 左侧切 `编程` -> `配置资源`，先配置 `通用工控机` / `Generic IPC` 的 Spider/SPIDR URL。该资源用于证明 WFC 可部署到端侧执行器，不等同于 Wearedge Agent Service。
4. 在资源配置页展开 `用户设备`，拖入 `自定义资源`，命名为 `Wearedge Agent Service`，定义 `agentHost`、`agentPort` 等服务参数。
5. 回到工作流，左侧 `编程` -> `编程语言`，拖入 Python 程序块，命名为 `CallWearedgeDecisionApi`。
   关键操作：如果默认工作流主线上已有 `[占位]`，必须把 Python Block 拖到该占位块上完成替换；仅把 Python Block 放在画布空白处不会进入主线执行。
6. 在 Python Block 的属性面板中编辑输入输出：`input1` 为 `Resource` 并绑定 `Wearedge Agent Service`，`input2` 为 `JSON`，输出为 `JSON`。
7. 双击 Python Block，在代码模板的 Business Code 区域调用 `/v1/workflow-canvas/decision`。
8. 右侧打开 `数据表`，定义 `wearedgeDecision` 或拆分字段，拖入 `更新数据表` 功能块并绑定。
9. 运行/部署工作流，截取日志和 Dashboard/ui-builder 展示。

只读 CLI 辅助：

```powershell
python scripts/wfc_private_api_probe.py --project-id cmq6lbb9x00bx1l6pxll7voae --workflow-instance-id ryn.cmq6lbb9x00bx1l6pxll7voae.workflow1 --dry-run --json
```

该脚本只用于诊断 WFC 项目文件、Dashboard Explorer 和 log-manager 路径。真实请求必须通过本地环境变量临时提供 `WFC_COOKIE`，脚本会拒绝无 cookie 的非 dry-run 请求，并且不会打印 cookie 值。其输出只能作为内部备份/诊断，不能替代 live WFC 运行日志和 Dashboard 截图。

源码编辑注意：

- 如果顶部显示 `DEBUG`，`fb_main.py` 编辑器会进入只读状态，并提示 `Cannot edit in read-only editor`。先点击调试浮条的 stop 图标，使顶部恢复 `已保存` / `play-circle`，再打开源码编辑。
- 当前仓库提供可复制到 WFC `fb_main.py` 的 live-edit 参考源码：`workflows/wfc_call_wearedge_decision_fb_main.py`。该版本只使用标准库 `urllib.request` 调用临时 HTTPS Wearedge Agent Service，不包含平台账号、token 或密钥。
- 粘贴保存后，截图应同时覆盖 `fb_main.py`、`/v1/workflow-canvas/decision`、`wearedge_decision_ok` 日志标识和底部 `保存` 成功状态。
- 若 WFC 原生 log-manager 或 inline read 视图没有显示 stdout，可把 Wearedge gateway 中同一轮运行产生的外部 `POST /v1/workflow-canvas/decision` `200 OK` 作为辅助证据；这不能替代 `05-run-log-ok-true.png` 的 live WFC 原生日志要求。
- 2026-06-12 以后优先复制仓库中的短版 `workflows/wfc_call_wearedge_decision_fb_main.py`。该版本保持 `ok`、`latency_ms`、`selected_direction`、`approval_status` 和短 `competition_metrics` 输出，避免完整 API 响应导致 WFC 编辑器或输出面板过重。保存后必须复核源码窗口可见 `_summary` / `selected_direction`，或运行后数据表/日志出现这些字段，才能认定 live WFC 已使用短版。

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `gongyi-mofang/00-wfc-projects-authenticated.png` | 已登录项目页 | 展示 Workflow Canvas 项目页和 `新建空白项目` 入口，证明账号已具备 WFC 访问权限。 |
| `gongyi-mofang/01-resource-block-wearedge-agent-service.png` | 资源配置页 | 优先展示 `通用工控机` / Spider 执行器配置；若已创建自定义资源，则同时展示 `Wearedge Agent Service` 参数。 |
| `gongyi-mofang/02-python-function-block-call-api.png` | Python Function Block 编辑页 | 展示 `CallWearedgeDecisionApi` 调用 `/v1/workflow-canvas/decision`。 |
| `gongyi-mofang/03-global-data-table-decision-fields.png` | 全局数据表字段 | 展示主方向、优先级、建议动作、证据、指标、责任人、残余风险、人工确认状态。 |
| `gongyi-mofang/04-dashboard-decision-view.png` | Dashboard | 首选真实 WFC Dashboard/ui-builder；若使用 `docs/submission/dashboard-mock.html` 截图，必须标注为 fallback mock。 |
| `gongyi-mofang/05-run-log-ok-true.png` | 运行日志 | 首选真实 WFC log-manager 中的 `ok=true`、function blocks、latency 或写表记录；当前 fallback 图来自本地 `scripts/smoke_workflow_canvas_decision.py`，配套 `05-run-log-ok-true.fallback.json`，不能声称为 live WFC 成功日志。 |
| `gongyi-mofang/06-human-approval-gate.png` | 人工确认节点 | 首选真实 WFC 人工确认节点/Dashboard 确认项；若使用 Dashboard mock 截图，必须标注为 fallback mock。 |

真实截图替换流程：

1. 把三张真实 WFC PNG 截图放入忽略目录 `submission-assets/live-evidence/gongyi-mofang-live-source/`。
2. 文件名使用下列任一组：
   `04-dashboard-decision-view.png` / `dashboard-decision-view.png` / `dashboard.png`；
   `05-run-log-ok-true.png` / `run-log-ok-true.png` / `run-log.png`；
   `06-human-approval-gate.png` / `human-approval-gate.png` / `approval-gate.png`。
3. 为每张截图创建同名 `.review.json` 复核侧车，文件也放在 staging 目录。命名示例：

```text
04-dashboard-decision-view.png
04-dashboard-decision-view.review.json
05-run-log-ok-true.png
05-run-log-ok-true.review.json
06-human-approval-gate.png
06-human-approval-gate.review.json
```

4. `.review.json` 必须确认 `live_wfc_source=true`，`source_url` 来自 `https://wfc.bd-iiot.com/` 或 `https://spidr.wfc.bd-iiot.com/`，并记录 UTC 截图时间和观察到的 live 信号。示例：

```json
{
  "live_wfc_source": true,
  "source_url": "https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae",
  "captured_at_utc": "2026-06-12T10:30:00Z",
  "reviewer_role": "WFC operator",
  "observed_signals": ["wearedge_decision_ok", "latency"]
}
```

5. 三类截图的最低复核信号：

| 目标 | `observed_signals` 要求 |
| --- | --- |
| Dashboard | 必须同时包含 `metric_cards`、`decision_path`、`approval_items`、`workflow_state`。 |
| Run log | 至少包含 `ok=true`、`wearedge_decision_ok`、`latency`、`function_block_output`、`table_writeback` 之一。 |
| HumanApprovalGate | 至少包含 `pending`、`approved`、`rejected`、`human_confirmation`、`approval_status` 之一。 |

6. 人工复核画面确实来自 live WFC 后运行：

```powershell
python scripts/promote_wfc_live_evidence.py --confirm-live-source --require-review-sidecars --operator-note "reviewed live WFC screenshots"
python scripts/verify_live_evidence.py --stage platform --write-manifest
python scripts/verify_finals_foundation.py --json
```

`promote_wfc_live_evidence.py` 会覆盖核心 04/05/06 截图，删除对应 `.fallback.json/.fallback.html` 标记，并写入 `wfc-live-evidence-replacement-manifest.json`。没有 `--confirm-live-source` 时脚本会拒绝执行；加上 `--require-review-sidecars` 后，脚本还会拒绝没有 live WFC 来源 URL、UTC 截图时间和目标信号的截图，防止把 mock 或 smoke test 图误标成 live 平台证据。

Dashboard 路径备注：

- `https://wfc.bd-iiot.com/dashboard-explorer` 当前是 Dashboard 预览/列表页。若接口返回空，会显示 `No Dashboard`，页面本身不提供新建入口。
- 前端路由读取 `/api/projects/dashboard-explorer`，有数据时通过 `/remote/preview?...` 加载已有 Dashboard。
- 因此 Dashboard 证据应从 WFC 工作流运行实例和 ui-builder 创建路径获得，而不是在 Dashboard Explorer 空页里继续盲点。

已采集的辅助截图可用于视频素材和操作复盘，不替代上表核心 0-6 项：

| 文件名 | 用途 |
| --- | --- |
| `gongyi-mofang/07-wfc-project-create-form-filled.png` | 项目创建表单，含项目名称与描述。 |
| `gongyi-mofang/08-wfc-project-created-card.png` | `Wearedge WFC PoC` 项目卡创建成功。 |
| `gongyi-mofang/09-wfc-project-editor-opened.png` | 项目编辑器已打开。 |
| `gongyi-mofang/10-wfc-expanded-project-baseline.png` | 扩大视图后的资源配置基线。 |
| `gongyi-mofang/11-wfc-workflow-canvas-active.png` | 工作流主画布可见。 |
| `gongyi-mofang/12-wfc-programming-library-open.png` | 编程功能块库可见。 |
| `gongyi-mofang/17-wfc-function-block-properties.png` | 右侧属性面板/数据表入口可见。 |
| `gongyi-mofang/95-wfc-debug-state-spidr-open.png` | WFC 已进入 `DEBUG` 状态，执行器显示 `https://spidr.wfc.bd-iiot.com`；只作为调试状态辅助证据。 |
| `gongyi-mofang/96-wfc-run-log-workflow-ready.png` | 运行日志弹窗辅助证据；iframe 曾读取到 `Workflow is ready.`，还不是 `ok=true` API 成功日志。 |
| `gongyi-mofang/debug-current-for-coordinate.png` | 2026-06-11 调试态坐标排查图；仅作为操作审计，不作为提交核心证据。 |
| `gongyi-mofang/102-wfc-python-fb-main-saved.png` | 2026-06-11 已把仓库中的 `workflows/wfc_call_wearedge_decision_fb_main.py` 粘贴并保存到 live WFC `fb_main.py`。 |
| `gongyi-mofang/103-wfc-log-manager-after-python-run.png` | log-manager 页面读取到 `Workflow is ready.`。 |
| `gongyi-mofang/104-wfc-log-manager-after-debug-trigger.png` | 调试触发后的 log-manager 辅助证据，仍未形成 `ok=true`。 |
| `gongyi-mofang/105-wfc-debug-stopped-after-run-attempt.png` | 调试运行尝试后已停止，避免平台会话长时间挂起。 |
| `gongyi-mofang/108-wfc-dashboard-explorer-live-20260612.png` | Dashboard Explorer live 复核，当前显示 `No Dashboard`。 |
| `gongyi-mofang/110-wfc-data-table-fields-drawer-live-20260612.png` | WFC 数据表抽屉 live 截图，显示 8 个 Wearedge 决策字段。 |
| `gongyi-mofang/116-wfc-drag-python-onto-placeholder-20260612.png` | 将 Python Block 拖到 `[占位]` 上完成主线替换的操作证据。 |
| `gongyi-mofang/118-wfc-spidr-post-200-gateway-log-20260612.png` | WFC/SPIDR 调用 Wearedge API 后，gateway 端记录外部 `POST 200 OK` 的辅助证据。 |
| `gongyi-mofang/119-wfc-connected-python-block-final-saved-20260612.png` | Python Block 已成为工作流主线节点并保存。 |
| `gongyi-mofang/120-wfc-debug-read-state-after-live-run-20260612.png` | WFC 运行后的 DEBUG/read 状态；平台视图仍未显示 `ok=true` 文本。 |
| `gongyi-mofang/121-wfc-programming-tab-selected-20260612.png` | WFC `编程` 页辅助截图；当前视图未展开可编辑文件树。 |

## 端侧运行证据截图

| 文件名 | 画面要求 | 说明 |
| --- | --- | --- |
| `edge-runtime/01-healthz.png` | `/healthz` 或服务启动终端 | 证明 Wearedge Agent Service 已运行。 |
| `edge-runtime/02-runtime-profile.png` | `/v1/edge/runtime-profile` 输出 | 展示 Jetson / IPC / local server 部署能力和安全边界。 |
| `edge-runtime/05-solution-profile.png` | `/v1/industrial-agent/solution-profile` 输出 | 展示工业问题、Gemma 4 E2B/llama.cpp 模型角色、KPI 决策矩阵和 HumanApprovalGate。 |
| `edge-runtime/03-workflow-canvas-decision-smoke.png` | `scripts/smoke_workflow_canvas_decision.py` 输出 | 证明 WFC decision API 可跑通。 |
| `edge-runtime/04-jetson-ipc-local-node.png` | Jetson、IPC、本地工控机或边缘服务器画面 | 证明智能体运行时可放在端侧算力中；如果硬件未到位，用本地工控机/边缘服务器证据替代。 |
| `edge-runtime/06-http-resource-benchmark.json` | HTTP+资源 benchmark JSON | 由 `scripts/collect_edge_runtime_evidence.py` 生成，包含 `/v1/workflow-canvas/decision` HTTP 延迟、CPU/RSS/系统内存和平台信息。 |
| `edge-runtime/07-edge-runtime-evidence-manifest.md` | Edge runtime evidence manifest | 汇总 benchmark 路径、p95/max、资源采样和 Jetson/IPC 复跑边界。 |

端侧 benchmark 采集：

```powershell
python scripts/benchmark_local_gateway_latency.py
python scripts/collect_edge_runtime_evidence.py
```

Jetson / IPC 复跑：

```bash
python scripts/collect_edge_runtime_evidence.py --rerun-benchmark --iterations 20 --final-edge-node
```

Windows 侧可用一条命令远程完成 Jetson 部署、benchmark、`tegrastats` 和证据拉回：

```powershell
$env:JETSON_SSH_PASSWORD = "<本地设置，不提交>"
python scripts/collect_jetson_edge_evidence.py --host wearedge-pro.local --user ryn --iterations 20
Remove-Item Env:\JETSON_SSH_PASSWORD
```

Jetson 上也可手动同时打开 `tegrastats --interval 1000`，把日志保存到 `submission-assets/live-evidence/edge-runtime/08-tegrastats-http-resource-benchmark.log`。

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
