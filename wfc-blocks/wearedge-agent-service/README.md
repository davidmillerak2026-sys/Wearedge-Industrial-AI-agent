# Wearedge Agent Service WFC Resource Block Prototype

更新日期：2026-06-09

## Purpose

This prototype shows how Wearedge can be exposed as a Gongyi Mofang Workflow Canvas resource block. The intended deployment is an edge Agent Runtime running on Jetson, Siemens Edge IPC, local industrial PC, or a cloud/API World proxy.

## Parameters

| Parameter | Example | Notes |
| --- | --- | --- |
| `agentHost` | `127.0.0.1` | Jetson/IPC/local server host or API World proxy host. |
| `agentPort` | `8081` | FastAPI gateway port. |
| `apiKeyRef` | `WEAREDGE_DEMO_TOKEN` | Optional bearer token or secret reference. |
| `deploymentMode` | `jetson` | One of `jetson`, `ipc`, `local_server`, `cloud_proxy`. |
| `plantId` | `demo-plant-01` | Plant context. |
| `lineId` | `pkg-line-3` | Production line context. |

## Function Block

`function-blocks/CallWearedgeDecisionApi.py` calls:

```text
POST /v1/workflow-canvas/decision
```

It returns:

| Output | Type | Purpose |
| --- | --- | --- |
| `decision_json` | JSON | Full Wearedge response for data table and Dashboard. |
| `primary_direction` | string | Main decision direction. |
| `requires_human_confirmation` | boolean | Routes high-risk actions to `HumanApprovalGate`. |
| `error_message` | string | HTTP or schema failure message. |

## Safety Boundary

The block must not write directly to PLC, robot, or quality-release outputs. It should write decision state to a global data table and route high-risk actions through Workflow Canvas approval blocks.

## Packaging

Preferred deterministic package command:

```powershell
python scripts/package_wfc_resource_block.py --json
```

The default output is an ignored local deliverable:

```text
submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/wearedge-agent-service-0.1.0.zip
submission-assets/live-evidence/gongyi-mofang/wfc-resource-package/wearedge-agent-service-0.1.0.package-manifest.json
```

Legacy PowerShell helper:

```powershell
.\package.ps1
```

The generated `.zip` is a local deliverable and should not be committed unless selected as an explicit submission artifact.
