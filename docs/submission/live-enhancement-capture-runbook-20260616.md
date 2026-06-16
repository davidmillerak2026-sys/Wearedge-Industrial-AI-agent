# 三项增强证据取证作业单

更新日期：2026-06-16

目标：补齐当前夺冠级增强项，但不把临时 PoC、localhost、mock 或未完成 GUI 操作误写成最终 live 证据。

## 当前结论

| 增强项 | 当前状态 | 本轮判断 |
| --- | --- | --- |
| 稳定 HTTPS endpoint | API 合同已可通过本地预检，缺固定 HTTPS host | 不能靠 `localhost`、`loca.lt`、`trycloudflare.com`、`ngrok-free.app` 写成稳定证据。 |
| Xcelerator Console live 调试 | 已确认 API 详情页代理基址与代理路径；接口 debug 调用仍待补 | 需要用真实稳定后端替换占位 server 后，再补 live debug/test 调用截图。 |
| WFC 动态数据表写回 | 已有 live `ok=true`、`fields_ready` 和 `更新数据表.1` 字段承载 | 还差 `输出1 -> 更新数据表.1` 数据线或原生数据表值动态变化截图。 |

## 1. 稳定 HTTPS Endpoint

### 不能算稳定的地址

以下只能写作临时 PoC，不可作为最终稳定复现地址：

- `http://127.0.0.1:*`
- `http://localhost:*`
- `*.loca.lt`
- `*.trycloudflare.com`
- `*.ngrok-free.app`
- 任何一次性随机 tunnel

### 可接受路线

| 路线 | 需要什么 | 适用情况 |
| --- | --- | --- |
| 企业 HTTPS 网关 | 固定域名、证书、Nginx/反向代理、可访问的 Wearedge gateway | 有云服务器、企业网关或边缘服务器。 |
| Cloudflare Named Tunnel | Cloudflare 账号、一个可控域名、named tunnel DNS 绑定 | 没有公网 IP，但有域名和 Cloudflare。 |
| Xcelerator API World Proxy | Xcelerator 提供稳定代理地址，且后端 server URL 是公网 HTTPS | 平台代理可被调试/订阅调用。 |

### 验收命令

拿到固定 HTTPS 地址后运行：

```powershell
python scripts/verify_stable_wearedge_endpoint.py --base-url https://<stable-host> --write-evidence
```

验收文件：

```text
submission-assets/live-evidence/stable-endpoint/stable-endpoint-evidence.json
submission-assets/live-evidence/stable-endpoint/stable-endpoint-evidence.md
```

验收信号：

- `ready=true`
- `endpoint.evidence_tier=stable_https`
- `healthz` OK
- `runtime_profile` OK
- `workflow_canvas_decision` OK
- `competition_metrics.latency_target_met=true`

### 如果今天要人工补齐

请二选一：

1. 提供一个固定域名/服务器/Cloudflare Named Tunnel 的登录能力或已经绑定好的 hostname。
2. 在 Xcelerator Console 中确认是否存在“平台代理/调试调用地址”，并截图该代理 URL。若它只是服务注册路径但仍要求后端 server URL，则仍然需要第 1 条。

## 2. Xcelerator Console Live 调试截图

### 目标截图

保存到：

```text
submission-assets/live-evidence/xcelerator/
```

推荐文件名：

```text
44-xcelerator-runtime-profile-debug-live-20260616.png
44-xcelerator-runtime-profile-debug-live-20260616.review.json
45-xcelerator-workflow-decision-debug-live-20260616.png
45-xcelerator-workflow-decision-debug-live-20260616.review.json
```

### 手动路径

1. 打开 Xcelerator Console。
2. 进入 `Wearedge Workflow Canvas 协同决策 API` 服务草稿。
3. 进入接口信息、调试、测试、试调用或类似页面。
4. 对 `GET /v1/edge/runtime-profile` 发起调用。
5. 截图响应结果，确保画面出现：
   - `ok=true`
   - `workflow_canvas_ready=true` 或 `edge_capabilities.workflow_canvas_ready=true`
   - `model_direct_ot_control=false`
   - 服务仍为草稿/租户内时，不要写成已公开发布。
6. 对 `POST /v1/workflow-canvas/decision` 发起调用，payload 使用 `workflows/wearedge_wfc_poc_payload.json`。
7. 截图响应结果，确保画面出现：
   - `ok=true`
   - `competition_metrics.latency_target_met=true`
   - `collaborative_decision.primary_direction`
   - `workflow_canvas.function_blocks`

### 安全边界

- 不截 AppSecret。
- 不截完整手机号、身份证、营业执照号码或私人邮箱。
- 如页面包含 AppID，可只保留顶部服务名和接口返回区域，或打码。
- 若只是本地 JSON 预检，不要命名为 Xcelerator live 调用。

### Review sidecar 示例

```json
{
  "live_xcelerator_source": true,
  "source_url": "https://developers.siemens-x.com.cn/",
  "captured_at_utc": "2026-06-16T09:30:00Z",
  "reviewer_role": "Xcelerator operator",
  "observed_signals": [
    "api_service_draft",
    "runtime_profile_ok",
    "workflow_canvas_ready",
    "model_direct_ot_control_false"
  ],
  "redaction": "No AppSecret or private credentials captured."
}
```

## 3. WFC 动态数据表写回截图

### 目标截图

保存到：

```text
submission-assets/live-evidence/gongyi-mofang/
```

推荐文件名：

```text
197-wfc-data-table-values-after-python-writeback-20260616.png
197-wfc-data-table-values-after-python-writeback-20260616.review.json
198-wfc-output1-to-update-table-data-wire-20260616.png
198-wfc-output1-to-update-table-data-wire-20260616.review.json
```

### 最短手动路径

1. 打开 WFC 项目 `Wearedge WFC PoC`。
2. 如果顶部是 `DEBUG`，先停止运行，恢复到 `已保存` 或可编辑状态。
3. 确认画布上可见：
   - `CallWearedgeDecisionApi`
   - `更新数据表.1`
4. 建立数据端口连接：
   - 从 `CallWearedgeDecisionApi` 的 `输出1` 数据端口拖到 `更新数据表.1` 的输入数据端口。
   - 目标是数据连接虚线，不是黄色控制流线。
   - 不要拖动功能块本体；若功能块移动了，立即撤销。
5. 截图 `198`：画面需要同时显示两个块和中间数据线。
6. 点击运行/DEBUG。
7. 等 `CallWearedgeDecisionApi` 输出 `ok=true` 或 `状态码 Good`。
8. 打开数据表或 `更新数据表.1` 运行后值面板。
9. 截图 `197`：画面需要出现 Python 输出后的动态值，例如：
   - `selected_direction=maintenance`
   - `approval_status=pending_human_approval`
   - `recommended_action=...`
   - `latency_ms=<本次运行值>`

### 如果 GUI 连接仍然太难

请不要继续反复拖拽。改走两条备选证据：

1. 从 WFC 导出 workflow/project JSON，交给我运行：

```powershell
python scripts/analyze_wfc_workflow_bindings.py <exported-workflow.json> --require-confirmed
```

2. 截图 WFC 原生运行日志里 `CallWearedgeDecisionApi.output` 的 `fields_ready`，同时截图 `更新数据表.1` 的字段绑定面板。材料口径写成“动态输出已准备，原生数据端口连接待平台复现”，不夸大为完成写表。

### Review sidecar 示例

`197`：

```json
{
  "live_wfc_source": true,
  "source_url": "https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae",
  "captured_at_utc": "2026-06-16T09:45:00Z",
  "reviewer_role": "WFC operator",
  "observed_signals": [
    "data_table_values",
    "selected_direction",
    "approval_status",
    "latency_ms",
    "after_python_output"
  ],
  "redaction": "No WFC password, cookie, token, or private credential captured."
}
```

`198`：

```json
{
  "live_wfc_source": true,
  "source_url": "https://wfc.bd-iiot.com/project/cmq6lbb9x00bx1l6pxll7voae",
  "captured_at_utc": "2026-06-16T09:40:00Z",
  "reviewer_role": "WFC operator",
  "observed_signals": [
    "CallWearedgeDecisionApi",
    "UpdateDataTable",
    "output1_to_update_table_data_wire"
  ],
  "redaction": "No WFC password, cookie, token, or private credential captured."
}
```

## 完成后三条验证

```powershell
python scripts/verify_stable_wearedge_endpoint.py --base-url https://<stable-host> --write-evidence
python scripts/verify_live_evidence.py --stage final --allow-missing --write-manifest
python scripts/generate_final_action_board.py --write --json
```

如果只补到了截图、还没有稳定 host，则跳过第一条，保留 `stable-endpoint` 为 `needs_stable_endpoint`。

## 2026-06-16 Xcelerator 已确认信息

已登录 Xcelerator API 详情页确认：

```text
服务名称：Wearedge Workflow Canvas 协同决策 API
状态：未发布
平台代理基址：https://apig.developers.siemens-x.com.cn
系统生成代理路径：/scps4pw78kj6B2PFEmZX
稳定平台代理 URL：https://apig.developers.siemens-x.com.cn/scps4pw78kj6B2PFEmZX
可见范围：租户内
所属应用：Wearedge 工业智能体服务
后端服务器地址：仍为 https://wearedge-agent-service.example.com 占位
服务器路径：/v1
```

结论：Xcelerator 稳定代理入口已经存在，但还不能算 Wearedge 稳定 endpoint 闭环。下一步要把后端服务器地址替换成真实稳定 HTTPS Wearedge Agent Service，再运行 verifier。
