import json
import logging
import ssl
import urllib.request


class ParamInput:
    def __init__(self, data: dict):
        self.input1 = data.get("input1")
        self.input2 = data.get("input2")


class ParamOutput:
    def __init__(self):
        self.output1 = None
        self.status = None
        self.ok = None
        self.latency_ms = None
        self.selected_direction = None
        self.approval_status = None


class FunctionBlock():
    def __init__(
        self,
        input_data: dict,
        set_output_callback,
        update_data_table_callback,
        update_global_table_callback,
        get_global_table_callback,
        **kwargs
    ):
        self.input_data = input_data
        self.set_output_callback = set_output_callback
        self.update_data_table_callback = update_data_table_callback
        self.update_global_table_callback = update_global_table_callback
        self.get_global_table_callback = get_global_table_callback
        self.kwargs = kwargs
        self.param_output = ParamOutput()

    def _json(self, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            return json.loads(value)
        return {}

    def _payload(self):
        return {
            "stage": "wfc_live_debug",
            "selected_directions": ["maintenance", "quality", "energy", "flexible_production", "workflow_canvas"],
            "context": {
                "maintenance": {"f1_pct": 88, "warning_lead_time_hours": 30, "root_cause_top3_pct": 92},
                "quality": {"detection_confidence_pct": 93, "relative_improvement_pct": 6},
                "energy": {"forecast_accuracy_pct": 96, "saving_pct": 12},
                "production": {"schedule_efficiency_gain_pct": 22, "component_reuse_pct": 76},
                "workflow_canvas": {"existing_component_use_pct": 72, "new_component_reuse_potential_pct": 80},
            },
        }

    def _base_url(self, resource):
        base_url = resource.get("baseUrl") or resource.get("agentUrl")
        if base_url:
            return str(base_url).strip().rstrip("/")
        host = str(resource.get("agentHost") or resource.get("host") or "").strip()
        if not host:
            raise ValueError("missing Wearedge Agent Service baseUrl or agentHost")
        if not host.startswith(("http://", "https://")):
            host = "http://" + host
        authority = host.split("//", 1)[-1].split("/", 1)[0]
        port = str(resource.get("agentPort") or "").strip()
        if port and ":" not in authority:
            host = host.rstrip("/") + ":" + port
        return host.rstrip("/")

    def _request(self):
        resource = self._json(self.param_input.input1)
        payload = self._json(self.param_input.input2) or self._payload()
        if not payload.get("selected_directions"):
            payload = self._payload()
        base_url = self._base_url(resource)
        return base_url.rstrip("/") + "/v1/workflow-canvas/decision", payload

    def _summary(self, result):
        decision = result.get("collaborative_decision") or {}
        metrics = result.get("competition_metrics") or {}
        wfc = result.get("workflow_canvas") or {}
        approval_status = "pending" if decision.get("requires_human_confirmation") else "not_required"
        return {
            "ok": bool(result.get("ok")),
            "latency_ms": result.get("latency_ms"),
            "selected_direction": decision.get("primary_direction"),
            "priority": decision.get("priority"),
            "recommended_action": decision.get("recommendation"),
            "evidence_summary": "WFC/SPIDR called Wearedge decision API",
            "competition_metrics": {
                "decision_accuracy_pct_estimate": metrics.get("decision_accuracy_pct_estimate"),
                "latency_target_met": metrics.get("latency_target_met"),
                "final_min_agent_directions_met": metrics.get("final_min_agent_directions_met"),
            },
            "owner": "line_engineer",
            "residual_risk": decision.get("residual_risk"),
            "approval_status": approval_status,
            "required_confirmations": (decision.get("required_confirmations") or [])[:5],
            "workflow_function_blocks": (wfc.get("function_blocks") or [])[:8],
        }

    def run(self):
        try:
            self.param_input = ParamInput(self.input_data)
            endpoint, payload = self._request()
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "bypass-tunnel-reminder": "1"},
                method="POST",
            )
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(request, timeout=15, context=context) as response:
                summary = self._summary(json.loads(response.read().decode("utf-8")))
            logging.info("wearedge_decision_ok=%s latency_ms=%s", summary["ok"], summary["latency_ms"])
            print("wearedge_decision_ok", summary["ok"], "latency_ms", summary["latency_ms"])
            self.param_output.output1 = json.dumps(summary, ensure_ascii=False)
            self.param_output.status = "Good" if summary["ok"] else "Bad"
            self.param_output.ok = summary["ok"]
            self.param_output.latency_ms = summary["latency_ms"]
            self.param_output.selected_direction = summary["selected_direction"]
            self.param_output.approval_status = summary["approval_status"]
        except Exception as exc:
            logging.error("Function block failed with exception: %s", exc)
            self.param_output.output1 = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
            self.param_output.status = "Bad"
            self.param_output.ok = False
        finally:
            self.set_output_callback(self.param_output)
