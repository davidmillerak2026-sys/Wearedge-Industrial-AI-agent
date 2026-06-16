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

### 2026-06-16 GUI 继续执行结果

本次继续按 live WFC 页面尝试建立 `CallWearedgeDecisionApi 输出1 -> 更新数据表.1 输入` 数据端口连接。浏览器画布中可以看到 `CallWearedgeDecisionApi` 和 `更新数据表.1`，但端口坐标仍不稳定：一次拖拽没有形成清晰虚线数据连接，而是移动了 Python Function Block。已立即执行撤销，后续截图确认画布恢复到原位置且保持 `已保存` 状态。

本次不把 WFC 原生动态写表记为完成。当前完成级别仍是：

- live WFC `CallWearedgeDecisionApi.output` 返回 `ok=true`。
- 输出 JSON 包含 `wfc_writeback.method=wfc_output1_to_update_data_table`。
- 输出 JSON 包含 `fields_ready`，说明 Python 侧已经准备好写表字段。
- `更新数据表.1` 可承载 Wearedge 决策字段，并已在真实 WFC DEBUG 中证明字段锁定和数据表目标存在。

下一次最短闭环路线：

1. 从 WFC 导出 workflow/project JSON，运行 `scripts/analyze_wfc_workflow_bindings.py <workflow.json> --require-confirmed`，用结构化文件确认数据线。
2. 或人工在 WFC GUI 中精确建立 `输出1 -> 更新数据表.1` 虚线数据连接后，截图 `198-wfc-output1-to-update-table-data-wire-20260616.png`。
3. 再运行 DEBUG，截图 `197-wfc-data-table-values-after-python-writeback-20260616.png`，证明原生数据表值与 `fields_ready` 一致。

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
- 兼容 `/v1/edge/runtime-profile` 中顶层 `workflow_canvas_ready=True` 或嵌套 `edge_capabilities.workflow_canvas_ready=True`。

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

### 2026-06-16 稳定 endpoint 执行结果

本次已新增稳定 endpoint 部署包：

```text
deploy/stable-endpoint/
```

其中包括：

- `README.md`：企业 HTTPS 网关、Cloudflare Named Tunnel、Xcelerator API World Proxy 三条路线。
- `nginx-wearedge.conf.template`：面向固定域名和 TLS 证书的反向代理模板。
- `cloudflared-config.yml.template`：面向 Cloudflare Named Tunnel 的稳定域名模板。

同时已用本地 `http://127.0.0.1:8081` 跑通 API 合同预检：`/healthz`、`/v1/edge/runtime-profile`、`/v1/workflow-canvas/decision` 均可返回有效结果。由于该地址不是非临时 HTTPS，verifier 会按预期保留唯一失败项：

```text
endpoint is not stable HTTPS; use only as temporary PoC evidence
```

因此当前结论是：代码和 API 合同已经准备好，稳定复现证据还需要固定 HTTPS 域名、Cloudflare Named Tunnel 绑定域名，或 Xcelerator API World 代理地址。

## C. Xcelerator 调试调用截图

当前已存在 Xcelerator 应用草稿、API 服务草稿和 4 个接口导入截图。2026-06-16 重新打开 `https://developers.siemens-x.com.cn/integration/api` 时页面回到登录态，因此本次没有继续进行 Console 内 live 调试调用，也没有保存任何账号、密钥或 AppSecret。

本次已生成可用于 Xcelerator 调试前核对的本地 API 预检响应，存放在 ignored live-evidence 目录：

```text
submission-assets/live-evidence/xcelerator/41-local-api-debug-response-for-xcelerator.json
```

该文件只能作为“待放入 Xcelerator 调试面板的 API 预检素材”，不能替代 Xcelerator Console live 调用截图。正式证据仍需在重新登录后完成：

1. 打开 API 服务草稿。
2. 使用稳定 HTTPS host 或 Xcelerator proxy 调用 `/v1/edge/runtime-profile`。
3. 调用 `/v1/workflow-canvas/decision`。
4. 截图保存到 `submission-assets/live-evidence/xcelerator/`，并在材料中标注服务仍为草稿/租户内或已授权范围。

## 提交口径

当前初赛材料建议这样写：

```text
Wearedge 已完成 Xcelerator / 工易魔方接入路径和 live WFC ok=true 运行日志证据。WFC 数据表已创建 Wearedge 决策字段，更新数据表块已完成静态字段承载和调试态截图。2026-06-16 新版 Function Block 已在真实 WFC DEBUG 中通过 HTTPS 调用 Wearedge API，输出 ok=true、状态码 Good，并给出 wfc_writeback 路由状态和 fields_ready 字段；后续将在平台环境稳定建立 输出1 -> 更新数据表.1 数据端口连接，并补充原生数据表值变化截图。
```

稳定 endpoint 建议这样写：

```text
当前已完成 OpenAPI 草稿、端侧 Jetson FastAPI 证据和临时 HTTPS PoC 外部可达验证。正式联合 PoC 阶段将切换为稳定 HTTPS endpoint 或 Xcelerator API World 代理地址，并用 endpoint verifier 输出可复验证据。
```
