# M400 图片推理接口契约

本文档定义 Vuzix M400 或其他可穿戴采图设备接入 WearEdge Pro Jetson 网关的最小稳定协议。目标是先把“设备采图 -> Jetson 推理 -> 五类结构化 agent 建议”跑通：Hazard Exposure、lao-shi-fu predictive maintenance、iQC、General WI 和 Changeover，再逐步加入 AR 展示、语音播报、质量 hold、转产确认和工单系统。

## Endpoint

```text
POST http://JETSON_IP:8081/v1/infer
Authorization: Bearer <DEMO_TOKEN>
Content-Type: multipart/form-data
```

## Form Fields

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `prompt` | 是 | 任务 Prompt。网关会按 `analysis_mode` 自动补齐并硬化输出契约。 |
| `image` | 是 | JPEG 或 PNG 图片。当前默认最大 4MB。 |
| `device_id` | 否 | 设备编号，例如 `m400-demo-01`。不传时默认为 `web-demo`。 |
| `frame_ts` | 否 | 设备侧采图时间，例如设备生成的 ISO 时间戳。 |
| `location_hint` | 否 | 场景位置，例如 `demo-zone` 或 `line-3-pump-room`。 |
| `capture_mode` | 否 | 采图模式，例如 `camera2-manual-trigger`、`manual-trigger`、`voice-trigger`。 |
| `analysis_mode` | 否 | `hazard`、`maintenance`、`iqc`、`wi` 或 `changeover`。默认 `hazard`。兼容别名：`safety`/`hazard_exposure` -> `hazard`，`lao_shi_fu`/`predictive_maintenance` -> `maintenance`，`quality` -> `iqc`，`work_instruction` -> `wi`。 |
| `needs_ocr` | 否 | `true/false`，当本帧需要读 HMI、小字、铭牌或标签时设为 `true`，用于生成视觉 token 预算建议。 |
| `high_detail` | 否 | `true/false`，当质检或设备细节需要更高视觉保真度时设为 `true`。 |
| `audio_seconds` | 否 | 当前语音片段秒数，默认 `0`；用于判断是否可走后续 vLLM/NIM 音频融合路线。 |
| `detector_evidence_json` | 否 | 仅 iQC 使用。M400 或边缘检测器可上传 JSON 字符串，包含 `product_id` 与 `detections[]` 的 defect class、confidence、bbox。网关会规范化为 `wear-edge-iqc-detector-evidence.v1`。 |

所有设备元数据都会被后端清洗并限制长度，防止异常控制字符或过长字段污染日志。

## Hazard Exposure Response Shape

默认 `analysis_mode=hazard` 的合格响应示例：

```json
{
  "ok": true,
  "api_version": "wear-edge-infer.v1",
  "analysis_mode": "hazard",
  "request_id": "4f3b9f3f5f664b5292b2f6212c0f9a2b",
  "received_at": "server-generated UTC timestamp",
  "device": {
    "device_id": "m400-demo-01",
    "frame_ts": "device-generated timestamp",
    "location_hint": "demo-zone",
    "capture_mode": "camera2-manual-trigger"
  },
  "answer": "- Scene: ...\n- Risk: ...\n- Action: ...",
  "scene": "...",
  "risk": "...",
  "action": "...",
  "model": "gemma4",
  "latency_ms": 8000,
  "image_bytes": 3170693,
  "image_content_type": "image/jpeg",
  "modality_plan": {
    "visual_token_budget": {
      "recommended": {
        "min_tokens": 140,
        "max_tokens": 140,
        "reason": "large frame keeps more visual evidence"
      },
      "current_runtime": {
        "min_tokens": 70,
        "max_tokens": 70
      },
      "status": "requires_server_restart",
      "llama_env": {
        "LLAMA_IMAGE_MIN_TOKENS": "140",
        "LLAMA_IMAGE_MAX_TOKENS": "140"
      }
    },
    "audio_fusion": {
      "enabled": false,
      "runtime": "llama.cpp",
      "model_variant": "E2B",
      "max_audio_seconds": 30,
      "route": "vllm_or_nim",
      "reason": "E2B audio is intentionally kept out of the current llama.cpp Orin Nano path"
    }
  },
  "evidence_plan": {
    "version": "wear-edge-evidence-plan.v1",
    "mode": "hazard",
    "current_sources": [
      {"name": "m400_image", "kind": "edge_capture", "status": "available"},
      {"name": "device_context", "kind": "edge_metadata", "status": "available"},
      {"name": "ocr_attention", "kind": "runtime_hint", "status": "not_requested"},
      {"name": "high_detail_visual", "kind": "runtime_hint", "status": "not_requested"}
    ],
    "missing_tools": ["ppe_detector", "zone_geofence", "ehs_rules"],
    "policy": "Use deterministic safety escalation when exposure evidence is missing or severe."
  },
  "tool_plan": {
    "version": "wear-edge-tool-plan.v1",
    "mode": "hazard",
    "max_iterations": 1,
    "max_tool_calls": 3,
    "used_tool_calls": 0,
    "status": "missing_tool_connections",
    "selected_tools": ["ppe_detector", "zone_geofence", "ehs_rules"],
    "skipped_tools": [
      {"name": "ppe_detector", "kind": "vision_tool", "reason": "not_connected"},
      {"name": "zone_geofence", "kind": "ehs_tool", "reason": "not_connected"},
      {"name": "ehs_rules", "kind": "rules_tool", "reason": "not_connected"}
    ],
    "deferred_tools": []
  },
  "saved_path": null,
  "contract": {
    "ok": true,
    "type": "hazard",
    "repaired": false,
    "min_words": 16,
    "violations": []
  },
  "action_card": {
    "version": "wear-edge-action-card.v1",
    "mode": "hazard",
    "channel": "inspect_area",
    "title": "Inspect area before continuing",
    "priority": "low",
    "owner": "operator",
    "requires_human": false,
    "operator_message": "Inspect the area before continuing with controlled movement.",
    "integration_target": "safety_observation",
    "required_confirmations": ["area identity", "operator confirmation"],
    "evidence_fields": ["scene", "risk"]
  },
  "follow_up_plan": {
    "version": "wear-edge-follow-up-plan.v1",
    "mode": "hazard",
    "status": "not_required",
    "next_action": "review_action_card",
    "requests": []
  },
  "integration_event": {
    "version": "wear-edge-integration-event.v1",
    "event_type": "ehs.inspect_area.requested",
    "target": "safety_observation",
    "routing_key": "safety_observation.operator.inspect_area",
    "status": "ready_for_dispatch",
    "idempotency_key": "4f3b9f3f5f664b5292b2f6212c0f9a2b:safety_observation:inspect_area",
    "requires_human": false,
    "payload": {
      "request_id": "4f3b9f3f5f664b5292b2f6212c0f9a2b",
      "analysis_mode": "hazard",
      "device": {
        "device_id": "m400-demo-01",
        "location_hint": "demo-zone"
      },
      "action_card": "...same action_card object...",
      "follow_up_plan": "...same follow_up_plan object...",
      "evidence": {
        "scene": "...",
        "risk": "..."
      },
      "action": "..."
    }
  },
  "agently_trace": {
    "version": "wear-edge-agently-trace.v1",
    "triggerflow": {
      "definition_id": "m400_infer",
      "definition_version": "wear-edge-agently-flow.v1",
      "entrypoint": "m400_infer",
      "execution_state": "closed",
      "stages": [
        {"name": "normalize_agent", "layer": "workflow", "status": "completed"},
        {"name": "select_agent_route", "layer": "workflow", "status": "completed"},
        {"name": "plan_modality", "layer": "workflow", "status": "completed"},
        {"name": "collect_evidence", "layer": "workflow", "status": "completed"},
        {"name": "bounded_react_tools", "layer": "agent", "status": "completed"},
        {"name": "build_contract_prompt", "layer": "agent", "status": "completed"},
        {"name": "model_infer", "layer": "model", "status": "completed"},
        {"name": "validate_contract", "layer": "agent", "status": "completed"},
        {"name": "identify_context", "layer": "agent", "status": "completed"},
        {"name": "structure_action", "layer": "action", "status": "completed"},
        {"name": "uncertainty_guard", "layer": "action", "status": "skipped"},
        {"name": "build_action_card", "layer": "action", "status": "completed"},
        {"name": "build_follow_up_plan", "layer": "action", "status": "completed"},
        {"name": "build_integration_event", "layer": "action", "status": "ready_for_dispatch"},
        {"name": "close_execution", "layer": "workflow", "status": "completed"}
      ]
    },
    "action_runtime": {
      "action_logs": [
        {"stage": "model_infer", "action_type": "llama_chat_completion", "status": "completed"}
      ]
    }
  },
  "runtime_stream": {
    "version": "wear-edge-runtime-stream.v1",
    "definition_id": "m400_infer",
    "definition_version": "wear-edge-agently-flow.v1",
    "request_id": "4f3b9f3f5f664b5292b2f6212c0f9a2b",
    "mode": "hazard",
    "execution_state": "closed",
    "closed": true,
    "events": [
      {"sequence": 1, "event": "workflow.stage.completed", "stage": "normalize_agent", "status": "completed"},
      {"sequence": 2, "event": "workflow.stage.completed", "stage": "select_agent_route", "status": "completed"},
      {"sequence": 5, "event": "model.call.completed", "stage": "model_infer", "status": "completed"},
      {"sequence": 6, "event": "contract.validation.completed", "stage": "validate_contract", "status": "completed"},
      {"sequence": 9, "event": "action.card.created", "stage": "build_action_card", "status": "completed"},
      {"sequence": 10, "event": "follow_up.plan.created", "stage": "build_follow_up_plan", "status": "completed"},
      {"sequence": 11, "event": "integration.event.created", "stage": "build_integration_event", "status": "ready_for_dispatch"},
      {"sequence": 12, "event": "workflow.closed", "stage": "close_execution", "status": "completed"}
    ]
  },
  "agent_loop": {
    "version": "wear-edge-agent-loop.v1",
    "mode": "hazard",
    "validation_attempts": 1,
    "contract_repaired": false,
    "decision": {
      "channel": "inspect_area",
      "owner": "operator",
      "requires_human": false,
      "reason": "hazard action starts with Inspect"
    }
  },
  "audit": {
    "logged": true
  }
}
```

## Agent Loop Metadata

每次 `/v1/infer` 响应都会返回 `agent_loop`，用于让 M400、审计日志和后续工厂系统看到同一条确定性编排路径：

- `version`: 当前 loop contract，现为 `wear-edge-agent-loop.v1`
- `mode`: 规范化后的 agent mode
- `stages`: `normalize_agent`、`select_agent_route`、`collect_evidence`、`retrieve_maintenance_kb`、`retrieve_iqc_quality_plan`、`retrieve_released_wi_source`、`retrieve_changeover_checklist`、`evaluate_maintenance_thresholds`、`bounded_react_tools`、`build_contract_prompt`、`model_infer`、`validate_contract`、`repair_contract`、`identify_context`、`evaluate_iqc_quality_rules`、`evaluate_released_source`、`structure_action`、`uncertainty_guard`、`released_source_guard`、`build_action_card`、`build_follow_up_plan`
- `validation_attempts`: 模型输出契约校验次数，发生自动修复时通常为 `2`
- `contract_repaired`: 是否经历过一次 repair prompt
- `decision.channel`: 下游动作通道，例如 `expand_inspection`、`quality_hold`、`stop_production`、`schedule_maintenance`、`changeover_verification`
- `decision.owner`: 建议接手角色，例如 `operator`、`quality_engineer`、`maintenance_engineer`、`line_lead`
- `decision.requires_human`: 是否必须进入人工确认或审批
- `context_guard`: 当机台、SKU、产品、WI 来源或危险场景证据不足时，记录 `blocked_fields`，并把低控制动作提升到人工确认通道
- `source_evaluation`: WI/Changeover 的 released-source 检索和匹配结果；没有发布版 WI 或目标 SKU checklist 时禁止把建议降级为可信执行步骤

## Agently Trace

`agently_trace` 是 WearEdge 当前本地实现的 Agently/TriggerFlow 风格执行记录。它不会要求 Jetson 原型机安装完整 Agently runtime，但字段设计保持可映射：

- `triggerflow.entrypoint`: 当前入口为 `m400_infer`
- `triggerflow.definition_id/version`: 当前本地 Agently-style workflow 蓝图标识，可在 `/healthz` 的 `agently.flow_definition` 查看完整定义
- `triggerflow.stages`: 明确记录 normalize、route selection、modality planning、evidence collection、maintenance KB retrieval、IQC quality-plan retrieval、released WI/changeover source retrieval、threshold/source evaluation、bounded tool planning、prompt contract、model infer、validate/repair、context identification、uncertainty guard、action card 和 integration event 等阶段
- `action_runtime.action_logs`: 记录模型调用、repair 调用和 skipped tool call 等动作日志，不保存图片二进制
- `execution_state`: 当前同步请求完成后为 `closed`

后续接入 AgentEra/Agently 时，可把 `agently_trace.triggerflow.stages` 映射为 TriggerFlow definition/export，把 `action_runtime.action_logs` 映射为 Agently action runtime logs。

## Runtime Stream

`runtime_stream` 是给 M400 UI、审计查询和后续 Agently DevTools bridge 使用的稳定业务事件流。它不是原始 token stream，也不暴露模型 parser path；它从同一份 workflow stage/action log 派生，保证和 `agently_trace` 同源。

- `version`: 当前运行事件契约，现为 `wear-edge-runtime-stream.v1`
- `request_id`: 与 `/v1/infer` 响应和审计日志中的 `request_id` 一致
- `mode`: 规范化后的 agent mode
- `closed`: 同步推理请求完成后为 `true`
- `events[].sequence`: 单次 run 内递增序号，便于 M400 按顺序渲染
- `events[].event`: 稳定业务事件，例如 `workflow.stage.completed`、`model.call.completed`、`tool.call.skipped`、`contract.validation.completed`、`action.card.created`、`integration.event.created`、`workflow.closed`
- `events[].payload`: 阶段相关元数据，例如 contract violation、priority、integration target 或模型调用 latency；不保存图片二进制

M400 当前可先显示 `runtime_stream.events.length` 和最后一个事件；后续做 AR/语音体验时，可把 `action.card.created` 映射成屏幕行动卡，把 `workflow.closed` 映射成“本轮建议完成”提示。

可以用受 token 保护的只读接口单独查看当前 flow definition：

```text
GET http://JETSON_IP:8081/v1/agent-flow
Authorization: Bearer <DEMO_TOKEN>
```

响应中的 `flow_definition` 与 `/healthz.agently.flow_definition` 相同，便于 M400、运维脚本或后续 Agently DevTools 读取当前编排蓝图。重点字段：

- `supported_modes`: 当前 5 个 agent mode：`changeover`、`hazard`、`iqc`、`maintenance`、`wi`
- `stages`: TriggerFlow-style 阶段定义，覆盖 normalize、route selection、modality plan、evidence collection、maintenance KB retrieval、IQC quality-plan retrieval、released source retrieval、threshold/source evaluation、bounded tool planning、contract prompt、model infer、validate/repair、action card、integration event 和 close
- `mode_contracts`: 每个 agent 的结构化输出字段，例如 maintenance 需要 `machine/symptom/maintenance_risk/evidence_needed/action`
- `runtime_stream.events`: 后续 UI 或 DevTools 可订阅的业务事件语义，例如 `workflow.stage.completed`、`tool.call.skipped`、`action.card.created`、`follow_up.plan.created`、`workflow.closed`
- `determinism`: 工业级确定性约束，包括最多一次 repair、最多一轮/三次 tool call、校验后才映射 action、context/source guard 后才生成 action card、纯规则 action mapping 和 idempotency key 规则

## Context Guard

WearEdge 会在模型输出通过契约校验后，再做一次确定性上下文检查。该步骤不再调用模型，只检查结构化字段是否足以支持动作：

- maintenance: `machine` 未识别时，低控制动作会变成 `maintenance_identification_required`
- iQC: `product` 或 `quality_risk` 证据不足时，`pass/continue_production` 会变成 `quality_review`
- changeover: `machine`、`sku` 或 `changeover_step` 未识别时，不能直接进入 `controlled_changeover_step`
- WI: `machine` 或 `work_instruction` 来源不清时，不能直接进入 `guided_operation`
- released-source guard: WI 必须命中发布版作业指导来源，Changeover 必须命中目标 SKU 的发布版 checklist；否则动作会进入 `wi_source_required` 或 `changeover_source_required`
- hazard: `scene` 或 `risk` 不清时，不能把危险暴露降级为继续作业

如果原动作本身已经需要人工确认，例如质量 hold、停产、转产 verification，guard 会保留原通道并在 `decision.reason` 和 `context_guard.blocked_fields` 中记录证据缺口。

也可以查看最近 agent runs 的 runtime stream 摘要：

```text
GET http://JETSON_IP:8081/v1/agent-runs/recent?limit=5
Authorization: Bearer <DEMO_TOKEN>
```

该接口读取同一份 JSONL 审计日志，但只返回面向 agent loop 的摘要：`request_id`、`analysis_mode`、`runtime_stream`、`last_event`、`action_card`、`follow_up_plan` 和 `integration_event`。如果未开启 `WEAREDGE_EVENT_LOG`，返回 `enabled: false` 和空 `runs`。

## Modality Plan

`modality_plan` 是请求级多模态运行计划。当前网关不会在单次请求中热切换 `llama-server` 的启动参数，而是生成可审计建议：

- `visual_token_budget.recommended`: 根据 `analysis_mode`、图片大小、`needs_ocr` 和 `high_detail` 计算出的建议视觉 token 预算。
- `visual_token_budget.current_runtime`: 当前网关进程看到的 `LLAMA_IMAGE_MIN_TOKENS/MAX_TOKENS`。
- `visual_token_budget.status`: `matched` 表示当前 runtime 与建议一致；`requires_server_restart` 表示如需使用建议预算，应调整环境变量并重启模型服务。
- `audio_fusion`: 当前语音融合路线建议。Orin Nano 上的 `llama.cpp` E2B 路径默认只承载 image+text；原生 E2B/E4B audio 建议走 vLLM 或 NIM。

## Evidence Plan

`evidence_plan` 是 5 个 agent 的证据边界清单。当前 POC 默认包含 M400 图片、设备元数据、OCR/detail runtime hint；maintenance 的 `manual_kb`、iQC 的 `quality_plan`、WI 的 `wi_repository` 和 Changeover 的 `changeover_checklist` 已接成本地 RAG/KB。iQC 如果上传了 `detector_evidence_json`，`visual_defect_detector` 会被标记为 available；否则外部 detector、MCP、QMS、CMMS、MES 和 EHS 工具会先以 `missing_tools` 公开，防止模型把未接入证据说成已经验证。

- maintenance: 计划接入 `asset_registry`、`telemetry_history`、`manual_kb`、`work_order_history`
- iQC: 计划接入 `visual_defect_detector`、`quality_plan`、`lot_context`
- changeover: 已接本地 `changeover_checklist` released-source retrieval，计划继续接入 `sku_recipe` 和 `first_piece_plan`
- WI: 已接本地 `wi_repository` released-source retrieval，计划继续接入 `machine_identity`
- hazard: 计划接入 `ppe_detector`、`zone_geofence`、`ehs_rules`

`build_contract_prompt` 会把 evidence context 写入模型提示中：未列为 current source 的外部证据不得被模型声称已验证。真正的放行、停产、转产完成、维修排程和 EHS 升级仍由后端规则和人工确认决定。

## IQC Detector Evidence

iQC 的推荐路径是 detector-first：检测器先输出结构化证据，VLM 再解释可见上下文，最终 disposition 由 quality plan 和 deterministic guard 决定。

M400 或边缘检测器可以把以下 JSON 作为 `detector_evidence_json` 表单字段上传：

```json
{
  "source": "simulated_m400_detector",
  "product_id": "AL-HOUSING-L3",
  "detections": [
    {"class": "edge_burr", "confidence": 0.73, "bbox": [180, 450, 330, 535]},
    {"class": "sealing_face_scratch", "confidence": 0.84, "bbox": [610, 335, 775, 435]},
    {"class": "contamination", "confidence": 0.79, "bbox": [410, 560, 560, 650]}
  ]
}
```

网关响应会增加：

```json
{
  "detector_evidence": {
    "version": "wear-edge-iqc-detector-evidence.v1",
    "status": "available",
    "product_id": "AL-HOUSING-L3",
    "detection_count": 3
  },
  "quality_evaluation": {
    "detector_status": "provided",
    "status": "detector_or_plan_risk_detected",
    "recommended_channel": "quality_hold"
  }
}
```

如果没有上传 detector evidence，而 quality plan 要求 detector evidence 才能 pass，系统会把自动放行路径降级到 `quality_review`。

## Bounded Tool Plan

`tool_plan` 是 Agently/ReAct-style 工具循环的本地确定性骨架。当前 POC 已把 maintenance 的 `manual_kb`、iQC 的 `quality_plan`、WI 的 `wi_repository`、Changeover 的 `changeover_checklist` 和可选 `visual_defect_detector` evidence 接入本地执行路径；其他外部系统仍不直接调用，但会在 `bounded_react_tools` 阶段先选择最多 3 个相关工具，并把未接入工具记录为 skipped：

- `max_iterations`: 当前固定为 `1`，避免现场同步请求中出现无界工具循环
- `max_tool_calls`: 当前固定为 `3`，优先选择每个 agent 最关键的 evidence tools
- `selected_tools`: 本轮应该优先尝试的工具，例如 iQC 的 `visual_defect_detector/quality_plan/lot_context`
- `used_tool_calls`: 已执行工具数；maintenance session 命中本地 `manual_kb` 时通常为 `1`，iQC 同时命中 quality plan 与 detector evidence 时通常为 `2`，WI/Changeover 命中 released source 时通常为 `1`
- `skipped_tools`: 因 `not_connected` 暂时跳过的工具，会进入 `agently_trace.action_runtime.action_logs`
- `deferred_tools`: 超出工具预算的工具，不允许被模型当作证据引用

后续真正接 MCP、向量 RAG、视觉检测器或 QMS/CMMS/MES/EHS API 时，应替换该阶段的执行器，而不是绕过 `tool_plan`。这样 M400、审计日志和 Agently DevTools 看到的 workflow 形状保持稳定。

## Maintenance KB / RAG

lao-shi-fu agent 现在会在 `retrieve_maintenance_kb` 阶段检索本地预测性维护知识库：

```text
data/maintenance_kb/pkg_l3_gbx_03.json
```

当前样例 KB 包含 PKG-L3-GBX-03 的振动 RMS、温度、润滑、报警和操作员感官观察处理规则。命中后，响应会包含：

```json
{
  "knowledge_base": {
    "version": "wear-edge-maintenance-kb.v1",
    "status": "matched",
    "query_asset_id": "PKG-L3-GBX-03",
    "thresholds": {
      "vibration_rms_high_mm_s": 6.5,
      "gearbox_temperature_high_c": 75,
      "bearing_temperature_high_c": 70
    },
    "hits": [
      {
        "revision": "PM-KB-2026.05-demo",
        "section_id": "GBX-VIB-01",
        "section_title": "Gearbox vibration RMS escalation"
      }
    ]
  }
}
```

这些 KB 片段会进入模型 prompt，增强预测性维护判断；但它们仍是 reference evidence，不是放行权限。RAG 命中的结构化阈值还会进入 `evaluate_maintenance_thresholds`，由确定性代码和 accepted session evidence 做比对，返回：

```json
{
  "maintenance_evaluation": {
    "version": "wear-edge-maintenance-condition-eval.v1",
    "status": "breach_detected",
    "risk_level": "high",
    "recommended_channel": "maintenance_report",
    "breaches": [
      {
        "signal": "vibration_rms_mm_s",
        "observed": "7.2 mm/s",
        "threshold": "6.5 mm/s",
        "kb_source_id": "PM-KB-2026.05-demo#GBX-VIB-01"
      }
    ]
  }
}
```

最终根因、RUL、重启许可和维护放行仍被 `follow_up_plan.blocked_claims` 阻止，必须由维修工程师或正式系统确认。

## Released WI / Changeover Source Guard

General WI 和 Changeover 不允许只凭模型“看起来像某台机器”就给出可执行指导。网关会在 `retrieve_released_wi_source` 或 `retrieve_changeover_checklist` 阶段检索本地发布版来源：

```text
data/released_sources/cartoner_station_2_wi.json
data/released_sources/labeler_fl1_sku_c500_changeover.json
```

命中后，响应会包含：

```json
{
  "source_evaluation": {
    "version": "wear-edge-released-source-eval.v1",
    "status": "released_source_matched",
    "recommended_channel": "guided_operation",
    "requires_human": false,
    "matched_source_id": "WI-CARTONER-ST2"
  }
}
```

如果 WI 没有命中发布版作业指导，或 Changeover 没有命中目标 SKU checklist，`released_source_guard` 会把低控制动作升级到人工确认通道：

```json
{
  "source_evaluation": {
    "status": "blocked_completion_claim",
    "recommended_channel": "changeover_source_required",
    "requires_human": true,
    "missing_inputs": ["released changeover checklist"]
  },
  "action_card": {
    "channel": "changeover_source_required",
    "requires_human": true
  }
}
```

这一步的设计目标是：模型可以解释 M400 画面和操作员问题，但不能替代已发布 WI、转产 checklist、首件验证或质量放行权限。

## Action Card

`action_card` 是给 M400、QMS、CMMS、EHS 或转产 checklist 使用的确定性动作包。模型不会直接决定这些字段；后端根据受控输出契约和 `agent_loop.decision.channel` 映射生成：

- `version`: 当前动作包契约，现为 `wear-edge-action-card.v1`
- `title`: 给操作员或现场主管看的短标题
- `priority`: `critical`、`high`、`medium` 或 `low`
- `owner`: 建议接手角色
- `operator_message`: 可直接显示或语音播报的行动消息
- `integration_target`: 下游系统，例如 `qms_quality_event`、`maintenance_work_order`、`changeover_checklist`、`ehs_case`
- `required_confirmations`: 进入人工确认、审批或系统写入前必须补齐的确认项
- `evidence_fields`: 本次动作包使用到的结构化证据字段

## Follow-Up Plan

`follow_up_plan` 是给 M400 使用的多轮补证据任务清单。它由后端根据 mode、结构化字段、缺失工具和确定性 action channel 生成，不由模型自由决定：

- `version`: 当前补证据契约，现为 `wear-edge-follow-up-plan.v1`
- `status`: `operator_evidence_required`、`ready_for_human_confirmation`、`not_required` 或 `contract_failed`
- `next_action`: M400 下一步应执行的动作，例如 `collect_operator_evidence`
- `requests`: 可执行采集任务，每项包含 `id`、`capture_type`、`prompt`、`expected_fields`、`maps_to_tools` 和 `blocks_final_judgment`
- `blocked_claims`: 在证据补齐前禁止输出的结论，例如最终根因、RUL、重启许可或维护放行

maintenance 模式下，如果模型只稳定识别出报警或可见症状，但没有可靠数值，`follow_up_plan.requests` 会提示操作员继续拍摄资产铭牌、HMI/condition monitor、温度表、润滑记录、最近维修记录，并用语音或表单补充异响、异味、发热、抖动、漏油和开始时间。

## Maintenance Session Evidence Loop

lao-shi-fu agent 现在支持专用 session API，用于把多张 M400 照片和操作员感官反馈合并到同一个维护排查上下文中。普通 `/v1/infer` 仍保持兼容；当现场需要按老师傅方式逐步补证据时，M400 应使用：

```text
POST /v1/maintenance-sessions
POST /v1/maintenance-sessions/{session_id}/evidence
POST /v1/maintenance-sessions/{session_id}/infer
GET  /v1/maintenance-sessions/{session_id}/trace
```

推荐证据顺序：

```text
maintenance_asset_identity_photo
maintenance_condition_screen_photo
maintenance_temperature_gauge_photo
maintenance_lubrication_record_photo
maintenance_recent_work_record_photo
maintenance_operator_sensory_check
```

`/v1/maintenance-sessions/{session_id}/infer` 会强制走 `analysis_mode=maintenance`，并在 Agently-style workflow 中增加 `load_session_evidence`、`retrieve_maintenance_kb` 和 `evaluate_maintenance_thresholds` 阶段。它会把已接受证据、RAG 命中的维修知识库、阈值 breach 判断和仍缺失的 follow-up evidence 注入 prompt，同时写入 `agently_trace`、`runtime_stream`、`integration_event.payload` 和审计日志。详细契约见 [maintenance-session-evidence-loop.md](maintenance-session-evidence-loop.md)。

## Integration Event Envelope

`integration_event` 是下一步写入外部系统前的标准事件草案。当前网关只生成 envelope，不直接调用 QMS、CMMS、MES 或 EHS API：

- `version`: 当前事件契约，现为 `wear-edge-integration-event.v1`
- `event_type`: 按目标系统和动作通道生成，例如 `qms.quality_hold.requested`、`cmms.schedule_maintenance.requested`
- `target`: 与 `action_card.integration_target` 一致
- `routing_key`: 后续 outbox、消息队列或 webhook 可使用的路由键
- `status`: `pending_human_confirmation`、`ready_for_dispatch` 或 `no_external_action`
- `idempotency_key`: 由 `request_id`、`target` 和 `channel` 组成，防止重复写入外部系统
- `payload`: 包含 M400 设备上下文、action card、follow-up plan、结构化 evidence、maintenance KB/threshold evaluation、IQC quality evaluation、released source evaluation 和最终 action

## Lao-shi-fu Predictive Maintenance Response Shape

当 `analysis_mode=maintenance` 时，M400 用于识别机台、可见症状和预测性维护风险：

```json
{
  "ok": true,
  "analysis_mode": "maintenance",
  "machine": "Visible machine, cell, station, or unknown.",
  "symptom": "Visible symptom, abnormal condition, alarm context, or unknown.",
  "maintenance_risk": "Bounded equipment uptime, wear, leakage, vibration, heat, lubrication, or machine failure risk.",
  "evidence_needed": "Manual, signal, log, threshold, inspection point, or operator observation needed next.",
  "action": "Inspect the machine safely and report missing evidence to maintenance before increasing operating load.",
  "contract": {
    "ok": true,
    "type": "maintenance",
    "violations": []
  }
}
```

Maintenance 结果是“老师傅”式维护建议和证据清单，不是最终 RCA、EHS hazard 分析、停机许可或重启许可。人员暴露、PPE、堵塞通道、跌倒/夹伤、禁区或 geofence 等应在 loop 开始的 `select_agent_route` 阶段进入 `hazard` agent，而不是混入 `maintenance` agent。

当前 deterministic action map 对维护场景有一条额外升级规则：如果模型输出虽然以 `Inspect` 或 `Monitor` 开头，但结构化证据中出现黄色/琥珀 PLC 报警并伴随高振动、温升、油污/漏油、润滑不足或皮带磨损等设备条件，后端会把动作从 `condition_inspection` 提升为 `maintenance_report`；若出现红色报警、冒烟、燃烧气味、严重泄漏、急停、imminent mechanical failure、catastrophic component damage 或 urgent maintenance assessment 等设备维护关键字，则提升为 `maintenance_escalation`。单纯出现 `safety hazard` 字样不会触发 maintenance escalation；EHS hazard exposure 由 `hazard` agent 处理。这条规则不依赖模型自行决定优先级。

Maintenance agent 的生产形态应是 operator-in-the-loop 的多轮补证据流程，而不是单帧终局判断。第一轮 M400 图像用于识别机台、可见异常、仪表和报警；如果 `evidence_plan.missing_tools` 包含 `asset_registry`、`telemetry_history`、`manual_kb` 或 `work_order_history`，Jetson 会返回 `follow_up_plan.status=operator_evidence_required`，让 M400 逐项提示操作员继续补证据，例如拍摄润滑记录、最近维修表、HMI 报警详情、温度/振动显示，或语音/表单反馈异响、异味、发热、抖动、漏油等体感观察。Jetson 收到新增图片或观察后，应在同一个 request family 中重新生成维护 action card，最终再输出 `maintenance_report`、`maintenance_escalation`、`schedule_maintenance` 或 `condition_monitoring`。在缺少趋势、阈值和维修历史前，禁止输出确定 RUL、最终根因或重启许可。

## iQC Response Shape

当 `analysis_mode=iqc` 时，网关会强制模型返回过程质量检查字段：

```json
{
  "ok": true,
  "api_version": "wear-edge-infer.v1",
  "analysis_mode": "iqc",
  "request_id": "4f3b9f3f5f664b5292b2f6212c0f9a2b",
  "device": {
    "device_id": "m400-demo-01",
    "location_hint": "line-3-final-check",
    "capture_mode": "camera2-manual-trigger"
  },
  "answer": "- Product: ...\n- Quality Risk: ...\n- Disposition: expand_inspection\n- Action: ...",
  "product": "Visible product/process evidence from the M400 image.",
  "quality_risk": "Potential defect, process drift, contamination, mix-up, or no visible quality risk.",
  "disposition": "expand_inspection",
  "action": "Expand inspection to adjacent units from the same station lot and shift while holding suspect parts for quality engineer review.",
  "contract": {
    "ok": true,
    "type": "iqc",
    "repaired": false,
    "min_words": 16,
    "violations": []
  }
}
```

`disposition` 是受控枚举：

```text
pass
needs_review
expand_inspection
quality_hold
stop_production
rework
scrap
capa_request
```

iQC 结果是质量决策支持，不是最终放行或报废授权。涉及扩大翻检、停产、质量 hold、报废、CAPA 的动作，后续必须接入 QMS/MES 或质量工程师审批工具。

## WI Response Shape

当 `analysis_mode=wi` 时，M400 用于识别机台并回答操作员关于作业要点的问题：

```json
{
  "ok": true,
  "analysis_mode": "wi",
  "machine": "Visible machine, line, station, or unknown.",
  "work_instruction": "Operator-facing work instruction guidance based on visible context and the question.",
  "risk_control": "Safety or quality controls that must be respected before operating.",
  "action": "Confirm the machine identity and posted work instruction revision before applying any operation guidance.",
  "contract": {
    "ok": true,
    "type": "wi",
    "violations": []
  }
}
```

WI 结果只用于现场作业指导问答。涉及参数修改、绕过联锁、复位报警、上电重启或异常状态处理时，必须升级给班组长、工艺工程师或维修工程师。生产化路径必须让 `source_evaluation.status=released_source_matched` 后，才允许把低风险回答落到 `guided_operation`。

## Changeover Response Shape

当 `analysis_mode=changeover` 时，M400 用于识别机台和 SKU/recipe/标签上下文，并指导下一步转产动作：

```json
{
  "ok": true,
  "analysis_mode": "changeover",
  "machine": "Visible machine, line, station, or unknown.",
  "sku": "Visible current or target SKU, recipe, label, traveler, or unknown.",
  "changeover_step": "Next controlled conversion activity for the operator.",
  "verification": "Check needed before restart, startup, or first-piece release.",
  "action": "Confirm the target SKU and hold startup until first-piece verification is accepted by the authorized quality role.",
  "contract": {
    "ok": true,
    "type": "changeover",
    "violations": []
  }
}
```

Changeover 结果不能替代已发布转产 WI、工艺参数表、首件检验、线清场或质量放行权限。后续生产化应接入 SKU recipe、tooling matrix、line-clearance checklist 和 QMS first-piece approval。当前本地 released-source guard 要求目标 SKU checklist 命中后，才允许进入 `controlled_changeover_step`；否则返回 `changeover_source_required`。

## M400 最小客户端逻辑

第一版 APK 只需要做四件事：

1. 用 Camera2 获取一张 1280x720 JPEG。
2. 用 multipart/form-data 上传 `prompt`、`image`、`analysis_mode` 和设备元数据。
3. hazard 模式读取 `scene`、`risk`、`action`；maintenance 模式读取 `machine`、`symptom`、`maintenance_risk`、`evidence_needed`、`action`；iQC 模式读取 `product`、`quality_risk`、`disposition`、`action`；WI 模式读取 `machine`、`work_instruction`、`risk_control`、`action`；changeover 模式读取 `machine`、`sku`、`changeover_step`、`verification`、`action`。
4. 把 `action` 显示到 M400 屏幕，后续再接骨传导耳机播报。

## 本地模拟验收

在 Jetson 上使用固定图片模拟 M400 上传：

```bash
cd ~/WearEdge-Pro
source .env

TEST_IMAGE=/home/ryn/WearEdge-Pro/testdata/unsafety.jpeg \
DEMO_TOKEN="$DEMO_TOKEN" \
DEVICE_ID=m400-demo-01 \
LOCATION_HINT=demo-zone \
CAPTURE_MODE=manual-trigger \
scripts/smoke_test.sh
```

通过时必须看到：

```text
llama-server text health passed.
Gateway output contract passed.
```

并且响应 JSON 应包含：

```json
{
  "api_version": "wear-edge-infer.v1",
  "request_id": "...",
  "device": {
    "device_id": "m400-demo-01"
  },
  "contract": {
    "ok": true,
    "violations": []
  }
}
```

这一步完成后，M400 APK 的开发风险会明显降低，因为服务端协议、鉴权、图片上传、模型输出和验收标准都已经固定。

## Optional Audit Log

默认情况下，WearEdge Pro 不保存上传图片，也不写入推理事件日志。若演示或调试需要证明每一帧都可追踪，可以在 Jetson `.env` 中开启 JSONL 审计日志：

```bash
WEAREDGE_EVENT_LOG=/home/ryn/WearEdge-Pro/runtime/inference-events.jsonl
```

重启网关后：

```bash
sudo systemctl restart wearedge-gateway.service
```

每次合格推理会追加一行 JSON，包含：

- `request_id`
- `received_at`
- `analysis_mode`
- `device`
- `model`
- `latency_ms`
- `image_bytes`
- hazard: `scene`、`risk`
- maintenance: `machine`、`symptom`、`maintenance_risk`、`evidence_needed`
- iQC: `product`、`quality_risk`、`disposition`
- WI: `machine`、`work_instruction`、`risk_control`
- changeover: `machine`、`sku`、`changeover_step`、`verification`
- `action`
- `modality_plan`
- `evidence_plan`
- `tool_plan`
- `knowledge_base`
- `maintenance_evaluation`
- `follow_up_plan`
- `contract`
- `action_card`
- `integration_event`
- `agently_trace`
- `runtime_stream`
- `agent_loop`

审计日志不保存图片二进制内容，适合作为隐私优先的现场演示和工程复盘证据。

Jetson 实测结果：

```text
response.audit.logged -> true
request_id            -> 5b33c68044d748dda77b2a5546968c8f
event_log.request_id  -> 5b33c68044d748dda77b2a5546968c8f
event_log.saved_path  -> null
```

这说明 M400 或网页上传得到的 HTTP 响应可以和本地 JSONL 审计事件一一对应，同时原始图片没有被默认落盘。

## Recent Audit Query

开启 `WEAREDGE_EVENT_LOG` 后，可以用受 token 保护的只读接口查看最近审计事件：

```text
GET http://JETSON_IP:8081/v1/audit/recent?limit=5
Authorization: Bearer <DEMO_TOKEN>
```

响应示例：

```json
{
  "ok": true,
  "enabled": true,
  "limit": 5,
  "events": [
    {
      "event_type": "inference.completed",
      "request_id": "5b33c68044d748dda77b2a5546968c8f",
      "device": {
        "device_id": "m400-demo-01"
      },
      "contract": {
        "ok": true,
        "violations": []
      }
    }
  ]
}
```

该接口只返回最近事件，不暴露本地日志文件路径；如果审计日志未开启，会返回 `enabled: false` 和空事件列表。

M400 Android MVP 已内置 `Audit Recent` 按钮，调用该接口并显示：

- 最新审计事件的 `request_id`
- 本机最近一次推理响应的 `request_id`
- 两者是否匹配

这让现场演示不必切回电脑命令行，也能证明“眼镜端请求 -> Jetson 推理 -> 审计日志”被同一个 `request_id` 串起来。

## Android MVP Client

首版 M400 Android MVP 位于：

```text
clients/m400/android/
```

它用于验证真实可穿戴客户端路径：

```text
M400 Camera2 JPEG
  -> Android WearEdgeM400Client
  -> Jetson /v1/infer
  -> hazard: scene / risk / action
  -> maintenance: machine / symptom / maintenance_risk / evidence_needed / action
  -> iQC: product / quality_risk / disposition / action
  -> WI: machine / work_instruction / risk_control / action
  -> changeover: machine / sku / changeover_step / verification / action
  -> agent_loop decision channel / owner / requires_human
  -> action_card priority / integration_target / required_confirmations
  -> follow_up_plan status / requests / blocked_claims
  -> integration_event event_type / status / idempotency_key
  -> evidence_plan current/missing evidence
  -> tool_plan selected/skipped tool calls
  -> maintenance_evaluation threshold breaches / risk level
  -> agently_trace triggerflow stages / action logs
  -> runtime_stream event count / last event
  -> M400 screen display
```

当前版本已经使用 Camera2 打开应用内预览，并通过 `ImageReader` 捕获 JPEG；默认选择 16:9 且不超过 1280x720 的最大可用尺寸。它重点验证端到端协议、鉴权、图片上传、设备元数据、输出契约和审计追踪。M400 MVP 已支持输入 `analysis_mode=hazard`、`maintenance`、`iqc`、`wi` 或 `changeover`。后续生产化步骤是在真实 M400 上验证可用分辨率、对焦曝光行为、连续采集稳定性，以及 maintenance/iQC/WI/changeover 模式与设备信号、质量计划、作业指导书、SKU recipe 和 QMS 的审批闭环。
