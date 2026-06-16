# WFC 动态写回与稳定 Endpoint 补证闭环

更新日期：2026-06-16

## 结论

这两项都是夺冠级增强，不是当前初赛提交的硬阻塞项：

- WFC 动态数据表写回：当前已有 live WFC `ok=true` 运行日志、数据表字段、`更新数据表.1` 静态字段和调试态截图；2026-06-16 已补到新版 `CallWearedgeDecisionApi.output` 显示 `ok=true`、`状态码 Good`、`wfc_writeback.method=wfc_output1_to_update_data_table` 的 live 证据。还差“输出1 数据线驱动原生数据表值变化”的最终截图或导出 workflow 绑定证明。
- 稳定 API / 平台复现地址：当前已有 Xcelerator OpenAPI 草稿和临时 HTTPS PoC 证据；还差稳定 HTTPS endpoint 或平台代理可复现地址。

## A. WFC 动态数据表写回

### 现在已经补强的代码能力

`workflows/wfc_call_wearedge_decision_fb_main.py` 已增强，并按 WFC007 手册路线调整为“输出 JSON + 数据端口写表”：

- 调用 `/v1/workflow-canvas/decision` 后生成 compact summary。
- `param_output.output1` 保留 JSON 摘要，供 WFC 原生运行日志截图。
- 新增 `wfc_writeback` 状态字段。
- `wfc_writeback.method` 固定为 `wfc_output1_to_update_data_table`，提醒平台侧必须建立 `输出1 -> 更新数据表.1` 的数据端口连接。
- `wfc_writeback.fields_ready` 给出可写表字段：`selected_direction`、`priority`、`recommended_action`、`approval_status`、`latency_ms`。
- 2026-06-16 live 调试发现：在 Python 里直接调用 WFC callback 不是当前手册确认路径，可能导致 DEBUG 卡在运行态；后续不再把 direct callback 作为默认写表方式。
- 2026-06-16 live 重跑已通过临时 HTTPS endpoint 调用 `/v1/workflow-canvas/decision`，右侧属性面板 `输出1` 返回 `ok=true`，`状态码=Good`，并包含 `wfc_writeback.method=wfc_output1_to_update_data_table`。证据存放在 `submission-assets/live-evidence/gongyi-mofang/196-wfc-dynamic-writeback-output-ok-20260616.png`，完整 DOM 输出另存为同目录 `196-wfc-dynamic-output-ok-dom-20260616.json`。

### 什么证据算完成

当前已满足第 1 条输出证据；要把“动态数据表写回”升级为最终原生写表 proof，还需要满足第 2 或第 3 条：

1. WFC 原生运行日志或属性面板显示 `CallWearedgeDecisionApi.output` 中：
   - `"ok": true`
   - `"wfc_writeback": {"method": "wfc_output1_to_update_data_table", ...}`
   - `selected_direction` / `approval_status` / `latency_ms`
2. WFC 原生数据表运行后可见字段值发生变化，例如：
   - `selected_direction=maintenance`
   - `approval_status=pending`
   - `latency_ms=<真实运行值>`
3. 导出的 WFC workflow JSON 经脚本确认存在数据线：

```powershell
python scripts/analyze_wfc_workflow_bindings.py <exported-workflow.json> --require-confirmed
```

其中确认对象是：

```text
CallWearedgeDecisionApi 输出1 -> 更新数据表.1 输入
```

### 截图命名

建议把最终证据存入：

```text
submission-assets/live-evidence/gongyi-mofang/
```

推荐命名：

```text
196-wfc-dynamic-writeback-output-ok-20260616.png
197-wfc-data-table-values-after-python-writeback-20260616.png
198-wfc-output1-to-update-table-data-wire-20260616.png
```

## B. 稳定 API / 平台复现地址

### 什么算稳定

可作为强证据：

- 自有域名或企业可控域名的 HTTPS endpoint。
- Xcelerator API World 代理地址。
- Cloudflare Named Tunnel 绑定域名。
- 企业网关/边缘服务器的固定 HTTPS 地址。

只能作为临时 PoC，不应写成稳定 endpoint：

- `*.loca.lt`
- `*.trycloudflare.com`
- `*.ngrok-free.app`
- `localhost` / `127.0.0.1`
- 任何一次性随机 tunnel。

### 新增 verifier

新增脚本：

```powershell
python scripts/verify_stable_wearedge_endpoint.py --base-url https://<stable-host> --write-evidence
```

脚本会验证：

- `GET /healthz`
- `GET /v1/edge/runtime-profile`
- `POST /v1/workflow-canvas/decision`
- endpoint 是否为非临时 HTTPS。
- `workflow_canvas_ready=True`
- 决策 `ok=True`
- `competition_metrics.latency_target_met=True`

证据输出：

```text
submission-assets/live-evidence/stable-endpoint/stable-endpoint-evidence.json
submission-assets/live-evidence/stable-endpoint/stable-endpoint-evidence.md
```

### 安全边界

- 不在仓库保存 API token、AppSecret、WFC cookie 或登录密码。
- 未经负责人确认，不自动公开本地服务或启动长期公网 tunnel。
- Xcelerator 服务若仍为草稿/租户内，不写成“已公开上架”。
- 临时 HTTPS PoC 可写为“外部可达验证”，不可写为“稳定平台复现地址”。

## 提交口径

当前初赛材料建议这样写：

```text
Wearedge 已完成 Xcelerator / 工易魔方接入路径和 live WFC ok=true 运行日志证据。WFC 数据表已创建 Wearedge 决策字段，更新数据表块已完成静态字段承载和调试态截图。2026-06-16 新版 Function Block 已在真实 WFC DEBUG 中通过 HTTPS 调用 Wearedge API，输出 ok=true、状态码 Good，并给出 wfc_writeback 路由状态和 fields_ready 字段；后续将在平台环境稳定建立 输出1 -> 更新数据表.1 数据端口连接，并补充原生数据表值变化截图。
```

稳定 endpoint 建议这样写：

```text
当前已完成 OpenAPI 草稿、端侧 Jetson FastAPI 证据和临时 HTTPS PoC 外部可达验证。正式联合 PoC 阶段将切换为稳定 HTTPS endpoint 或 Xcelerator API World 代理地址，并用 endpoint verifier 输出可复验证据。
```
