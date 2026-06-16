# Cloud Run Stable Endpoint Runbook

Purpose: deploy the lightweight Wearedge competition API as a stable HTTPS backend for Xcelerator API World and Gongyi Mofang WFC.

This Cloud Run service is a **stable HTTPS proxy/runtime for platform PoC validation**. It exposes the deterministic competition decision path and runtime profile, but it does not replace the Jetson / IPC edge evidence for local multimodal inference.

## Service Shape

- Container file: `Dockerfile.cloudrun`
- Cloud Run service name: `wearedge-agent-service`
- Suggested region: `asia-east1`
- Project observed in console: `project-0fb33b45-8118-49ed-b8c`
- Auth mode: unauthenticated PoC endpoint, no secrets stored in repo
- Runtime mode: `WEAREDGE_DEPLOYMENT_MODE=cloud_proxy`

## Required Endpoints

```text
GET  /healthz
GET  /v1/edge/runtime-profile
POST /v1/workflow-canvas/decision
```

## Console Deployment Path

1. Open Cloud Run in the Google Cloud Console.
2. Choose **Deploy container**.
3. If using source deployment, select the GitHub repository:

```text
davidmillerak2026-sys/Wearedge-Industrial-AI-agent
```

4. Set the Dockerfile path:

```text
Dockerfile.cloudrun
```

5. Set service name:

```text
wearedge-agent-service
```

6. Set region:

```text
asia-east1
```

7. Allow unauthenticated invocations for PoC verification.
8. Set container port to `8080`.
9. Add environment variables:

```text
WEAREDGE_AUTH_DISABLED=true
WEAREDGE_DEPLOYMENT_MODE=cloud_proxy
WEAREDGE_EDGE_NODE_ID=wearedge-cloud-run-poc
LLAMA_MODEL=wearedge-competition-decision-runtime
WEAREDGE_MODEL_VARIANT=deterministic-competition-runtime
```

10. Deploy and copy the generated `https://...run.app` URL.

## Verification

Run from this repository:

```powershell
python scripts/verify_stable_wearedge_endpoint.py `
  --base-url https://<service-url>.run.app `
  --write-evidence
```

Expected result:

```text
Ready: True
Evidence tier: stable_https
healthz: HTTP 200
runtime_profile: HTTP 200
workflow_canvas_decision: HTTP 200
```

## Xcelerator Backend Setting

After verification, update the Xcelerator API service backend:

```text
Server address: https://<service-url>.run.app
Server path: /
```

Keep the service visibility as tenant/internal PoC until the organizer or Siemens team confirms publication requirements.

## Cloud Shell Deployment Path

Open Cloud Shell in the same Google Cloud project, then run:

```bash
git clone https://github.com/davidmillerak2026-sys/Wearedge-Industrial-AI-agent.git
cd Wearedge-Industrial-AI-agent
chmod +x deploy/cloud-run/cloud-shell-deploy.sh
PROJECT_ID=project-0fb33b45-8118-49ed-b8c REGION=asia-east1 deploy/cloud-run/cloud-shell-deploy.sh
```

The script enables Cloud Run, Cloud Build, and Artifact Registry APIs if needed, creates the `wearedge` Docker repository if missing, builds `Dockerfile.cloudrun`, deploys the service, and prints:

```text
WEAREDGE_CLOUD_RUN_URL=https://...
```
