# Cloud Run Stable Endpoint Evidence

Updated: 2026-06-16

## Result

Wearedge now has a stable HTTPS PoC backend on Google Cloud Run:

```text
https://wearedge-agent-service-863888677331.asia-east1.run.app
```

Verifier result:

```text
Ready: True
Evidence tier: stable_https
```

Validated endpoints:

| Check | Path | HTTP |
| --- | --- | ---: |
| Health | `/v1/healthz` | 200 |
| Edge runtime profile | `/v1/edge/runtime-profile` | 200 |
| Workflow Canvas decision | `/v1/workflow-canvas/decision` | 200 |

Evidence files are stored outside Git under:

```text
submission-assets/live-evidence/stable-endpoint/
```

Key evidence files:

```text
stable-endpoint-evidence.md
stable-endpoint-evidence.json
cloud-run-service-wearedge-agent-service-20260616.json
cloud-build-438fd867-20260616.json
```

## Deployment

- Project: `project-0fb33b45-8118-49ed-b8c`
- Region: `asia-east1`
- Cloud Run service: `wearedge-agent-service`
- Revision: `wearedge-agent-service-00002-n77`
- Build ID: `438fd867-5cb6-4e17-bf1b-69aa3ab6402f`
- Image: `asia-east1-docker.pkg.dev/project-0fb33b45-8118-49ed-b8c/wearedge/wearedge-agent-service:20260616101709`

## Boundary

This service is a stable HTTPS PoC backend for Xcelerator and Gongyi Mofang integration evidence. It runs the lightweight deterministic competition decision API. It does not replace Jetson / IPC edge evidence for local multimodal inference or production-line deployment.

For Xcelerator API service backend configuration, use:

```text
Server address: https://wearedge-agent-service-863888677331.asia-east1.run.app
Server path: /
```

2026-06-16 update: this backend address has been filled into the Xcelerator API service draft and screenshots were captured under `submission-assets/live-evidence/xcelerator/45-xcelerator-api-backend-cloud-run-filled-20260616.png` and `46-xcelerator-api-backend-cloud-run-after-save-20260616.png`. The tenant proxy is not yet an end-to-end proof: `scripts/verify_xcelerator_proxy.py --write-evidence` currently returns platform code `-107` (`Can not find selector`), so selector/API path binding remains pending.
