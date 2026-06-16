# Stable HTTPS Endpoint Pack

Purpose: expose the Wearedge Agent Service through a stable HTTPS URL that Siemens Xcelerator API World and Gongyi Mofang WFC can call repeatedly.

This directory contains templates only. Do not commit tokens, tunnel credentials, TLS private keys, AppSecret values, or platform cookies.

## Target

The final endpoint must pass:

```powershell
python scripts/verify_stable_wearedge_endpoint.py --base-url https://<stable-host> --write-evidence
```

The verifier calls:

- `GET /healthz`
- `GET /v1/edge/runtime-profile`
- `POST /v1/workflow-canvas/decision`

It rejects local or temporary tunnel hosts such as `127.0.0.1`, `localhost`, `*.loca.lt`, `*.trycloudflare.com`, and `*.ngrok-free.app`.

## Route A: Enterprise HTTPS Gateway

Use this when an enterprise VM, edge gateway, or reverse proxy can expose HTTPS.

1. Run Wearedge gateway on the edge node:

```bash
python -m uvicorn jetson.app:app --host 127.0.0.1 --port 8081
```

2. Configure Nginx using `nginx-wearedge.conf.template`.
3. Install a certificate from the enterprise CA or Let's Encrypt.
4. Validate:

```powershell
python scripts/verify_stable_wearedge_endpoint.py --base-url https://agent.example.com --write-evidence
```

## Route B: Cloudflare Named Tunnel

Use this when the site has a Cloudflare account and a domain. A quick tunnel is not enough; use a named tunnel bound to a DNS hostname.

1. Install `cloudflared`.
2. Authenticate locally with the enterprise Cloudflare account.
3. Create a named tunnel and route DNS:

```bash
cloudflared tunnel create wearedge-industrial-agent
cloudflared tunnel route dns wearedge-industrial-agent wearedge-agent.example.com
```

4. Copy `cloudflared-config.yml.template`, fill the tunnel id and credential file path outside Git, then run:

```bash
cloudflared tunnel --config cloudflared-config.yml run
```

5. Validate the stable hostname with `verify_stable_wearedge_endpoint.py`.

## Route C: Xcelerator API World Proxy

Use this when Siemens Xcelerator API World provides a stable tenant or API proxy URL.

1. Keep the API service unpublished until the team confirms visibility and security.
2. Replace the OpenAPI `servers[0].url` with the approved stable Wearedge host or Xcelerator proxy URL.
3. Use the Xcelerator console debug/test panel to call `/v1/edge/runtime-profile` and `/v1/workflow-canvas/decision`.
4. Capture screenshots under `submission-assets/live-evidence/xcelerator/`.
5. Validate the same base URL with `verify_stable_wearedge_endpoint.py` if it is externally callable.

## Evidence Boundary

- Temporary tunnel evidence can support a PoC story but is not stable endpoint proof.
- Stable proof requires a non-temporary HTTPS hostname and verifier output.
- Xcelerator proxy proof requires live console screenshots; local API responses alone are only preflight evidence.
