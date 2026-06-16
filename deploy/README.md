# Deployment

Deployment templates for running WearEdge Pro services on the Jetson edge node.

| Path | Purpose |
| --- | --- |
| [`systemd/wearedge-llama.service`](systemd/wearedge-llama.service) | Starts the local llama.cpp multimodal model server. |
| [`systemd/wearedge-gateway.service`](systemd/wearedge-gateway.service) | Starts the FastAPI gateway that M400 and other clients call. |
| [`stable-endpoint/`](stable-endpoint/) | Templates for exposing the Wearedge gateway through a stable HTTPS endpoint for Xcelerator/WFC evidence. |

## Notes

- These files are templates. Update `User`, `WorkingDirectory`, and `EnvironmentFile` for the target Jetson account before installing.
- The current PoC has been verified with the service pair enabled after reboot.
- Keep production secrets in `.env` or a deployment secret store, not in Git.

See [`../docs/e2b-deployment-runbook.md`](../docs/e2b-deployment-runbook.md) for the full setup flow.
