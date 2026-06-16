# Xcelerator 代理验证记录

更新日期：2026-06-16

## 当前结果

已完成 Google Cloud Run 稳定 HTTPS 后端：

```text
https://wearedge-agent-service-863888677331.asia-east1.run.app
```

已在 Xcelerator API 服务草稿页面把 `服务器地址` 从占位地址替换为 Cloud Run 地址，并把 `服务器路径` 调整为 `/`，避免与 OpenAPI 中的 `/v1/...` 路径重复。

已截图：

```text
submission-assets/live-evidence/xcelerator/45-xcelerator-api-backend-cloud-run-filled-20260616.png
submission-assets/live-evidence/xcelerator/46-xcelerator-api-backend-cloud-run-after-save-20260616.png
```

Xcelerator 租户内代理地址当前仍未通过端到端验证：

```text
https://apig.developers.siemens-x.com.cn/scps4pw78kj6B2PFEmZX
```

直接调用结果：

```json
{
  "code": -107,
  "msg": "divide:Can not find selector, please check your configuration!",
  "bizMessage": null
}
```

## 判断

这说明 Cloud Run 后端已经稳定可达，但 Xcelerator API World 代理层仍缺少 selector/path 绑定或接口调试配置。当前不能把 `apig.developers.siemens-x.com.cn/scps4pw78kj6B2PFEmZX` 写成“已完成平台代理端到端验证”，只能写成“租户内代理草稿已建立，后端已回填，代理 selector 配置待平台调通”。

## 可复验脚本

新增：

```powershell
python scripts/verify_xcelerator_proxy.py --write-evidence
```

脚本验证：

- `GET /v1/edge/runtime-profile`
- `GET /v1/healthz`
- `POST /v1/workflow-canvas/decision`

输出：

```text
submission-assets/live-evidence/xcelerator/xcelerator-proxy-verification.json
submission-assets/live-evidence/xcelerator/xcelerator-proxy-verification.md
```

## 下一步

1. 在 Xcelerator API 服务的接口信息页确认 selector/API path 是否与 OpenAPI `/v1/...` 一致。
2. 若平台要求 `服务器路径=/v1`，则需要把导入接口路径调整为无 `/v1` 前缀，避免路径重复。
3. 使用 Console 调试面板调用 `GET /v1/edge/runtime-profile` 和 `POST /v1/workflow-canvas/decision`，拿到 Wearedge `ok=true` 响应截图。
4. 保持服务为租户内草稿，不公开发布，不提交密钥或企业敏感信息。
