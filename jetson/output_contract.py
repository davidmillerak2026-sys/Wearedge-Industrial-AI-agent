from __future__ import annotations

import re
from dataclasses import dataclass


ACTION_STARTERS = ("Stop", "Inspect", "Wear", "Keep", "Report")
IQC_ACTION_STARTERS = ("Pass", "Continue", "Inspect", "Expand", "Hold", "Stop", "Rework", "Scrap", "Report", "Escalate")
IQC_DISPOSITIONS = (
    "pass",
    "needs_review",
    "expand_inspection",
    "quality_hold",
    "stop_production",
    "rework",
    "scrap",
    "capa_request",
)
IQC_DISPOSITION_ACTION_STARTERS = {
    "pass": ("Pass", "Continue", "Report"),
    "needs_review": ("Inspect", "Report", "Escalate", "Hold"),
    "expand_inspection": ("Expand", "Inspect", "Hold", "Report"),
    "quality_hold": ("Hold", "Inspect", "Report", "Escalate"),
    "stop_production": ("Stop", "Report", "Escalate"),
    "rework": ("Rework", "Hold", "Inspect", "Report"),
    "scrap": ("Scrap", "Hold", "Report", "Escalate"),
    "capa_request": ("Report", "Escalate", "Hold"),
}
WI_ACTION_STARTERS = ("Inspect", "Confirm", "Follow", "Ask", "Report", "Escalate", "Stop", "Keep")
CHANGEOVER_ACTION_STARTERS = ("Confirm", "Inspect", "Set", "Change", "Verify", "Hold", "Stop", "Report", "Escalate")
MAINTENANCE_ACTION_STARTERS = ("Inspect", "Monitor", "Schedule", "Stop", "Report", "Escalate", "Keep")
ENERGY_ACTION_STARTERS = ("Inspect", "Reduce", "Shift", "Schedule", "Report", "Hold", "Keep")
DEFAULT_MIN_WORDS = 16

OUTPUT_CONTRACT_PROMPT = """Return exactly this format and nothing else:
- Scene: <detailed visible area description with at least sixteen words>
- Risk: <specific hazard exposure description with at least sixteen words>
- Action: <one safe next action for the operator with at least sixteen words>

Rules:
Scene must describe the visible place, people, equipment, obstruction, or work area using a complete sentence.
Risk must name a hazard and explain who or what could be exposed.
Action must start with Stop, Inspect, Wear, Keep, or Report.
Each line must be more than 15 words.
Do not add any introduction."""

IQC_OUTPUT_CONTRACT_PROMPT = """Return exactly this format and nothing else:
- Product: <visible product and in-process condition>
- Quality Risk: <suspected defect, process drift, contamination, mix-up, or no visible defect>
- Disposition: <pass|needs_review|expand_inspection|quality_hold|stop_production|rework|scrap|capa_request>
- Action: <one containment action for operator or quality engineer>

Rules:
Product must describe visible product/process evidence from the image.
Quality Risk must name a quality risk or say no visible quality risk.
Disposition must be exactly one allowed value.
Action must start with Pass, Continue, Inspect, Expand, Hold, Stop, Rework, Scrap, Report, or Escalate.
Each Product, Quality Risk, and Action line must be more than 15 words.
Do not invent tolerances, dimensions, sampling plans, release authority, or final customer disposition.
Do not add any introduction."""

WI_OUTPUT_CONTRACT_PROMPT = """Return exactly this format and nothing else:
- Machine: <identified machine, line, station, or unknown>
- Work Instruction: <operation points that answer the operator question>
- Risk Control: <safety or quality controls the operator must respect>
- Action: <one next action for the operator>

Rules:
Machine must identify the visible machine or say unknown when the image is insufficient.
Work Instruction must answer using operator-facing machine operation language.
Risk Control must mention safety, quality, tooling, energy, guard, parameter, or escalation controls.
Action must start with Inspect, Confirm, Follow, Ask, Report, Escalate, Stop, or Keep.
Each Work Instruction, Risk Control, and Action line must be more than 15 words.
Do not invent hidden machine state, parameters, lockout steps, or release authority.
Do not add any introduction."""

CHANGEOVER_OUTPUT_CONTRACT_PROMPT = """Return exactly this format and nothing else:
- Machine: <identified machine, line, station, or unknown>
- SKU: <visible current or target SKU, part number, recipe, label, or unknown>
- Changeover Step: <guided changeover step for the operator>
- Verification: <check before restart or first-piece release>
- Action: <one next action for the operator>

Rules:
Machine must identify the visible machine or say unknown when the image is insufficient.
SKU must identify visible SKU, recipe, label, part number, or say unknown.
Changeover Step must guide the next controlled conversion activity.
Verification must describe the check needed before restart, startup, or first-piece release.
Action must start with Confirm, Inspect, Set, Change, Verify, Hold, Stop, Report, or Escalate.
Each Changeover Step, Verification, and Action line must be more than 15 words.
Do not invent target SKU, tooling, recipe parameters, torque values, release authority, or first-piece approval.
Do not add any introduction."""

MAINTENANCE_OUTPUT_CONTRACT_PROMPT = """Return exactly this format and nothing else:
- Machine: <identified machine, cell, station, or unknown>
- Symptom: <visible symptom, abnormal condition, alarm context, or unknown>
- Maintenance Risk: <likely equipment uptime, wear, leakage, vibration, heat, lubrication, or machine failure risk>
- Evidence Needed: <manual, signal, log, threshold, inspection point, or operator observation needed next>
- Action: <one next action for operator or maintenance engineer>

Rules:
Machine must identify the visible equipment or say unknown when the image is insufficient.
Symptom must separate visible symptoms from inferred machine condition.
Maintenance Risk must describe bounded predictive-maintenance risk without claiming final root cause.
Maintenance Risk must not analyze EHS/personnel hazard exposure; that belongs to the hazard agent route.
Evidence Needed must name the missing manual, signal, log, threshold, or inspection evidence.
If visible numeric readings are unclear, Evidence Needed must request a closer HMI or gauge photo plus operator observation.
Action must start with Inspect, Monitor, Schedule, Stop, Report, Escalate, or Keep.
Each Symptom, Maintenance Risk, Evidence Needed, and Action line must be more than 15 words.
Do not invent thresholds, hidden sensor readings, root cause, work order authority, or restart permission.
Do not add any introduction."""

ENERGY_OUTPUT_CONTRACT_PROMPT = """Return exactly this format and nothing else:
- Asset: <identified line, cell, machine, utility load, or unknown>
- Energy Signal: <visible or provided load, idle, peak, forecast, compressed air, HVAC, or utility evidence>
- Optimization: <bounded energy-saving opportunity with production and quality constraints>
- Verification: <measurement, baseline, meter, schedule, or operator confirmation needed before action>
- Action: <one next action for operator, energy manager, or production lead>

Rules:
Asset must identify the line, machine, utility load, or say unknown when evidence is insufficient.
Energy Signal must separate measured or provided energy evidence from inferred operating condition.
Optimization must describe a bounded saving opportunity without claiming unverified savings.
Verification must name the baseline, meter, forecast, schedule, or confirmation needed before control.
Action must start with Inspect, Reduce, Shift, Schedule, Report, Hold, or Keep.
Each Energy Signal, Optimization, Verification, and Action line must be more than 15 words.
Do not invent utility tariffs, production permissions, PLC writes, savings percentages, or shutdown authority.
Do not add any introduction."""

_LABEL_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])?\s*(scene|risk|action)\s*:\s*(.+?)\s*$", re.IGNORECASE)
_IQC_LABEL_RE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*(product|quality\s+risk|disposition|action)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
_WI_LABEL_RE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*(machine|work\s+instruction|risk\s+control|action)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
_CHANGEOVER_LABEL_RE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*(machine|sku|changeover\s+step|verification|action)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
_MAINTENANCE_LABEL_RE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*(machine|symptom|maintenance\s+risk|evidence\s+needed|action)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
_ENERGY_LABEL_RE = re.compile(
    r"^\s*(?:[-*]|\d+[.)])?\s*(asset|energy\s+signal|optimization|verification|action)\s*:\s*(.+?)\s*$",
    re.IGNORECASE,
)
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?|[\u4e00-\u9fff]")


@dataclass(frozen=True)
class StructuredAnswer:
    scene: str
    risk: str
    action: str

    def as_text(self) -> str:
        return f"- Scene: {self.scene}\n- Risk: {self.risk}\n- Action: {self.action}"

    def as_dict(self) -> dict[str, str]:
        return {"scene": self.scene, "risk": self.risk, "action": self.action}


@dataclass(frozen=True)
class IQCStructuredAnswer:
    product: str
    quality_risk: str
    disposition: str
    action: str

    def as_text(self) -> str:
        return (
            f"- Product: {self.product}\n"
            f"- Quality Risk: {self.quality_risk}\n"
            f"- Disposition: {self.disposition}\n"
            f"- Action: {self.action}"
        )

    def as_dict(self) -> dict[str, str]:
        return {
            "product": self.product,
            "quality_risk": self.quality_risk,
            "disposition": self.disposition,
            "action": self.action,
        }


@dataclass(frozen=True)
class WIStructuredAnswer:
    machine: str
    work_instruction: str
    risk_control: str
    action: str

    def as_text(self) -> str:
        return (
            f"- Machine: {self.machine}\n"
            f"- Work Instruction: {self.work_instruction}\n"
            f"- Risk Control: {self.risk_control}\n"
            f"- Action: {self.action}"
        )


@dataclass(frozen=True)
class ChangeoverStructuredAnswer:
    machine: str
    sku: str
    changeover_step: str
    verification: str
    action: str

    def as_text(self) -> str:
        return (
            f"- Machine: {self.machine}\n"
            f"- SKU: {self.sku}\n"
            f"- Changeover Step: {self.changeover_step}\n"
            f"- Verification: {self.verification}\n"
            f"- Action: {self.action}"
        )


@dataclass(frozen=True)
class MaintenanceStructuredAnswer:
    machine: str
    symptom: str
    maintenance_risk: str
    evidence_needed: str
    action: str

    def as_text(self) -> str:
        return (
            f"- Machine: {self.machine}\n"
            f"- Symptom: {self.symptom}\n"
            f"- Maintenance Risk: {self.maintenance_risk}\n"
            f"- Evidence Needed: {self.evidence_needed}\n"
            f"- Action: {self.action}"
        )


@dataclass(frozen=True)
class EnergyStructuredAnswer:
    asset: str
    energy_signal: str
    optimization: str
    verification: str
    action: str

    def as_text(self) -> str:
        return (
            f"- Asset: {self.asset}\n"
            f"- Energy Signal: {self.energy_signal}\n"
            f"- Optimization: {self.optimization}\n"
            f"- Verification: {self.verification}\n"
            f"- Action: {self.action}"
        )


@dataclass(frozen=True)
class ContractCheck:
    ok: bool
    structured: (
        StructuredAnswer
        | IQCStructuredAnswer
        | WIStructuredAnswer
        | ChangeoverStructuredAnswer
        | MaintenanceStructuredAnswer
        | EnergyStructuredAnswer
        | None
    )
    violations: list[str]


def build_contract_prompt(prompt: str) -> str:
    stripped = prompt.strip()
    if _already_contains_contract(stripped):
        return _normalize_contract_word_rule(stripped)
    if not stripped:
        return OUTPUT_CONTRACT_PROMPT
    return f"{stripped}\n\n{OUTPUT_CONTRACT_PROMPT}"


def build_repair_prompt(previous_answer: str) -> str:
    return (
        "The previous answer did not satisfy the required output contract. "
        "Use the image and rewrite the answer.\n\n"
        f"{OUTPUT_CONTRACT_PROMPT}\n\n"
        "The words after Scene, Risk, and Action must each be more than 15 words. "
        "Use complete industrial safety sentences; do not use short phrases. "
        "Do not use a code block. Do not add explanations.\n\n"
        "Previous answer:\n"
        f"{previous_answer.strip()}"
    )


def build_iqc_contract_prompt(prompt: str) -> str:
    stripped = prompt.strip()
    if _already_contains_iqc_contract(stripped):
        return _normalize_contract_word_rule(stripped)
    if not stripped:
        return IQC_OUTPUT_CONTRACT_PROMPT
    return f"{stripped}\n\n{IQC_OUTPUT_CONTRACT_PROMPT}"


def build_iqc_repair_prompt(previous_answer: str) -> str:
    return (
        "The previous answer did not satisfy the required IQC output contract. "
        "Use the image and rewrite the answer.\n\n"
        f"{IQC_OUTPUT_CONTRACT_PROMPT}\n\n"
        "The words after Product, Quality Risk, and Action must be more than 15 words. "
        "Disposition must be one exact allowed value. Do not use a code block. Do not add explanations.\n\n"
        "Previous answer:\n"
        f"{previous_answer.strip()}"
    )


def build_wi_contract_prompt(prompt: str) -> str:
    stripped = prompt.strip()
    if _already_contains_wi_contract(stripped):
        return _normalize_contract_word_rule(stripped)
    if not stripped:
        return WI_OUTPUT_CONTRACT_PROMPT
    return f"{stripped}\n\n{WI_OUTPUT_CONTRACT_PROMPT}"


def build_wi_repair_prompt(previous_answer: str) -> str:
    return _build_named_repair_prompt("WI", WI_OUTPUT_CONTRACT_PROMPT, previous_answer)


def build_changeover_contract_prompt(prompt: str) -> str:
    stripped = prompt.strip()
    if _already_contains_changeover_contract(stripped):
        return _normalize_contract_word_rule(stripped)
    if not stripped:
        return CHANGEOVER_OUTPUT_CONTRACT_PROMPT
    return f"{stripped}\n\n{CHANGEOVER_OUTPUT_CONTRACT_PROMPT}"


def build_changeover_repair_prompt(previous_answer: str) -> str:
    return _build_named_repair_prompt("changeover", CHANGEOVER_OUTPUT_CONTRACT_PROMPT, previous_answer)


def build_maintenance_contract_prompt(prompt: str) -> str:
    stripped = prompt.strip()
    if _already_contains_maintenance_contract(stripped):
        return _normalize_contract_word_rule(stripped)
    if not stripped:
        return MAINTENANCE_OUTPUT_CONTRACT_PROMPT
    return f"{stripped}\n\n{MAINTENANCE_OUTPUT_CONTRACT_PROMPT}"


def build_maintenance_repair_prompt(previous_answer: str) -> str:
    return _build_named_repair_prompt("lao-shi-fu maintenance", MAINTENANCE_OUTPUT_CONTRACT_PROMPT, previous_answer)


def build_energy_contract_prompt(prompt: str) -> str:
    stripped = prompt.strip()
    if _already_contains_energy_contract(stripped):
        return _normalize_contract_word_rule(stripped)
    if not stripped:
        return ENERGY_OUTPUT_CONTRACT_PROMPT
    return f"{stripped}\n\n{ENERGY_OUTPUT_CONTRACT_PROMPT}"


def build_energy_repair_prompt(previous_answer: str) -> str:
    return _build_named_repair_prompt("energy management", ENERGY_OUTPUT_CONTRACT_PROMPT, previous_answer)


def check_output_contract(answer: str, *, min_words: int = DEFAULT_MIN_WORDS) -> ContractCheck:
    structured, parse_violations = parse_structured_answer(answer)
    violations = list(parse_violations)
    if structured is None:
        return ContractCheck(ok=False, structured=None, violations=violations)

    fields = structured.as_dict()
    for name, value in fields.items():
        count = count_words(value)
        if count < min_words:
            violations.append(f"{name} must contain at least {min_words} words; got {count}")

    action = structured.action.strip()
    if not any(action.lower().startswith(starter.lower()) for starter in ACTION_STARTERS):
        violations.append("action must start with Stop, Inspect, Wear, Keep, or Report")

    return ContractCheck(ok=not violations, structured=structured, violations=violations)


def check_iqc_output_contract(answer: str, *, min_words: int = DEFAULT_MIN_WORDS) -> ContractCheck:
    structured, parse_violations = parse_iqc_structured_answer(answer)
    violations = list(parse_violations)
    if structured is None:
        return ContractCheck(ok=False, structured=None, violations=violations)

    word_fields = {
        "product": structured.product,
        "quality_risk": structured.quality_risk,
        "action": structured.action,
    }
    for name, value in word_fields.items():
        count = count_words(value)
        if count < min_words:
            violations.append(f"{name} must contain at least {min_words} words; got {count}")

    disposition = structured.disposition.strip().lower()
    if disposition not in IQC_DISPOSITIONS:
        violations.append(f"disposition must be one of: {', '.join(IQC_DISPOSITIONS)}")

    action = structured.action.strip()
    if not any(action.lower().startswith(starter.lower()) for starter in IQC_ACTION_STARTERS):
        violations.append(
            "action must start with Pass, Continue, Inspect, Expand, Hold, Stop, Rework, Scrap, Report, or Escalate"
        )
    expected_starters = IQC_DISPOSITION_ACTION_STARTERS.get(disposition)
    if expected_starters and not any(action.lower().startswith(starter.lower()) for starter in expected_starters):
        violations.append(
            f"action for disposition={disposition} must start with one of: {', '.join(expected_starters)}"
        )

    return ContractCheck(ok=not violations, structured=structured, violations=violations)


def check_wi_output_contract(answer: str, *, min_words: int = DEFAULT_MIN_WORDS) -> ContractCheck:
    structured, parse_violations = parse_wi_structured_answer(answer)
    violations = list(parse_violations)
    if structured is None:
        return ContractCheck(ok=False, structured=None, violations=violations)

    for name, value in {
        "work_instruction": structured.work_instruction,
        "risk_control": structured.risk_control,
        "action": structured.action,
    }.items():
        count = count_words(value)
        if count < min_words:
            violations.append(f"{name} must contain at least {min_words} words; got {count}")
    if not any(structured.action.lower().startswith(starter.lower()) for starter in WI_ACTION_STARTERS):
        violations.append(f"action must start with one of: {', '.join(WI_ACTION_STARTERS)}")
    return ContractCheck(ok=not violations, structured=structured, violations=violations)


def check_changeover_output_contract(answer: str, *, min_words: int = DEFAULT_MIN_WORDS) -> ContractCheck:
    structured, parse_violations = parse_changeover_structured_answer(answer)
    violations = list(parse_violations)
    if structured is None:
        return ContractCheck(ok=False, structured=None, violations=violations)

    for name, value in {
        "changeover_step": structured.changeover_step,
        "verification": structured.verification,
        "action": structured.action,
    }.items():
        count = count_words(value)
        if count < min_words:
            violations.append(f"{name} must contain at least {min_words} words; got {count}")
    if not any(structured.action.lower().startswith(starter.lower()) for starter in CHANGEOVER_ACTION_STARTERS):
        violations.append(f"action must start with one of: {', '.join(CHANGEOVER_ACTION_STARTERS)}")
    return ContractCheck(ok=not violations, structured=structured, violations=violations)


def check_maintenance_output_contract(answer: str, *, min_words: int = DEFAULT_MIN_WORDS) -> ContractCheck:
    structured, parse_violations = parse_maintenance_structured_answer(answer)
    violations = list(parse_violations)
    if structured is None:
        return ContractCheck(ok=False, structured=None, violations=violations)

    for name, value in {
        "symptom": structured.symptom,
        "maintenance_risk": structured.maintenance_risk,
        "evidence_needed": structured.evidence_needed,
        "action": structured.action,
    }.items():
        count = count_words(value)
        if count < min_words:
            violations.append(f"{name} must contain at least {min_words} words; got {count}")
    if not any(structured.action.lower().startswith(starter.lower()) for starter in MAINTENANCE_ACTION_STARTERS):
        violations.append(f"action must start with one of: {', '.join(MAINTENANCE_ACTION_STARTERS)}")
    return ContractCheck(ok=not violations, structured=structured, violations=violations)


def check_energy_output_contract(answer: str, *, min_words: int = DEFAULT_MIN_WORDS) -> ContractCheck:
    structured, parse_violations = parse_energy_structured_answer(answer)
    violations = list(parse_violations)
    if structured is None:
        return ContractCheck(ok=False, structured=None, violations=violations)

    for name, value in {
        "energy_signal": structured.energy_signal,
        "optimization": structured.optimization,
        "verification": structured.verification,
        "action": structured.action,
    }.items():
        count = count_words(value)
        if count < min_words:
            violations.append(f"{name} must contain at least {min_words} words; got {count}")
    if not any(structured.action.lower().startswith(starter.lower()) for starter in ENERGY_ACTION_STARTERS):
        violations.append(f"action must start with one of: {', '.join(ENERGY_ACTION_STARTERS)}")
    return ContractCheck(ok=not violations, structured=structured, violations=violations)


def parse_structured_answer(answer: str) -> tuple[StructuredAnswer | None, list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line in _content_lines(answer):
        match = _LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower()
        if label in values:
            violations.append(f"duplicate {label} line")
            continue
        values[label] = _clean_value(match.group(2))

    missing = [label for label in ("scene", "risk", "action") if label not in values]
    if missing:
        violations.append(f"missing required line(s): {', '.join(missing)}")
        return None, violations

    return (
        StructuredAnswer(
            scene=values["scene"],
            risk=values["risk"],
            action=_normalize_action_starter(values["action"], ACTION_STARTERS, mode="hazard"),
        ),
        violations,
    )


def parse_iqc_structured_answer(answer: str) -> tuple[IQCStructuredAnswer | None, list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line in _content_lines(answer):
        match = _IQC_LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower().replace(" ", "_")
        if label in values:
            violations.append(f"duplicate {label} line")
            continue
        values[label] = _clean_value(match.group(2))

    missing = [label for label in ("product", "quality_risk", "disposition", "action") if label not in values]
    if missing:
        violations.append(f"missing required line(s): {', '.join(missing)}")
        return None, violations

    return (
        IQCStructuredAnswer(
            product=values["product"],
            quality_risk=values["quality_risk"],
            disposition=values["disposition"].lower(),
            action=_normalize_action_starter(
                values["action"],
                IQC_ACTION_STARTERS,
                mode="iqc",
                disposition=values["disposition"].lower(),
            ),
        ),
        violations,
    )


def parse_wi_structured_answer(answer: str) -> tuple[WIStructuredAnswer | None, list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line in _content_lines(answer):
        match = _WI_LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower().replace(" ", "_")
        if label in values:
            violations.append(f"duplicate {label} line")
            continue
        values[label] = _clean_value(match.group(2))
    missing = [label for label in ("machine", "work_instruction", "risk_control", "action") if label not in values]
    if missing:
        violations.append(f"missing required line(s): {', '.join(missing)}")
        return None, violations
    return (
        WIStructuredAnswer(
            machine=values["machine"],
            work_instruction=values["work_instruction"],
            risk_control=values["risk_control"],
            action=_normalize_action_starter(values["action"], WI_ACTION_STARTERS, mode="wi"),
        ),
        violations,
    )


def parse_changeover_structured_answer(answer: str) -> tuple[ChangeoverStructuredAnswer | None, list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line in _content_lines(answer):
        match = _CHANGEOVER_LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower().replace(" ", "_")
        if label in values:
            violations.append(f"duplicate {label} line")
            continue
        values[label] = _clean_value(match.group(2))
    missing = [label for label in ("machine", "sku", "changeover_step", "verification", "action") if label not in values]
    if missing:
        violations.append(f"missing required line(s): {', '.join(missing)}")
        return None, violations
    return (
        ChangeoverStructuredAnswer(
            machine=values["machine"],
            sku=values["sku"],
            changeover_step=values["changeover_step"],
            verification=values["verification"],
            action=_normalize_action_starter(values["action"], CHANGEOVER_ACTION_STARTERS, mode="changeover"),
        ),
        violations,
    )


def parse_maintenance_structured_answer(answer: str) -> tuple[MaintenanceStructuredAnswer | None, list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line in _content_lines(answer):
        match = _MAINTENANCE_LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower().replace(" ", "_")
        if label in values:
            violations.append(f"duplicate {label} line")
            continue
        values[label] = _clean_value(match.group(2))
    missing = [label for label in ("machine", "symptom", "maintenance_risk", "evidence_needed", "action") if label not in values]
    if missing:
        violations.append(f"missing required line(s): {', '.join(missing)}")
        return None, violations
    return (
        MaintenanceStructuredAnswer(
            machine=values["machine"],
            symptom=values["symptom"],
            maintenance_risk=values["maintenance_risk"],
            evidence_needed=values["evidence_needed"],
            action=_normalize_action_starter(values["action"], MAINTENANCE_ACTION_STARTERS, mode="maintenance"),
        ),
        violations,
    )


def parse_energy_structured_answer(answer: str) -> tuple[EnergyStructuredAnswer | None, list[str]]:
    values: dict[str, str] = {}
    violations: list[str] = []
    for line in _content_lines(answer):
        match = _ENERGY_LABEL_RE.match(line)
        if not match:
            continue
        label = match.group(1).lower().replace(" ", "_")
        if label in values:
            violations.append(f"duplicate {label} line")
            continue
        values[label] = _clean_value(match.group(2))
    missing = [label for label in ("asset", "energy_signal", "optimization", "verification", "action") if label not in values]
    if missing:
        violations.append(f"missing required line(s): {', '.join(missing)}")
        return None, violations
    return (
        EnergyStructuredAnswer(
            asset=values["asset"],
            energy_signal=values["energy_signal"],
            optimization=values["optimization"],
            verification=values["verification"],
            action=_normalize_action_starter(values["action"], ENERGY_ACTION_STARTERS, mode="energy"),
        ),
        violations,
    )


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _content_lines(answer: str) -> list[str]:
    lines: list[str] = []
    for raw_line in answer.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("```"):
            continue
        lines.append(line)
    return lines


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().strip("`")


def _normalize_action_starter(
    action: str,
    allowed_starters: tuple[str, ...],
    *,
    mode: str,
    disposition: str | None = None,
) -> str:
    cleaned = _clean_value(action)
    if any(cleaned.lower().startswith(starter.lower()) for starter in allowed_starters):
        return cleaned
    starter = _infer_action_starter(cleaned, mode=mode, disposition=disposition)
    if starter is not None and starter in allowed_starters:
        return f"{starter} {cleaned}"
    return cleaned


def _infer_action_starter(action: str, *, mode: str, disposition: str | None = None) -> str | None:
    text = action.lower()
    if _has_any(text, "escalate", "senior", "urgent", "升级", "上报高级", "紧急评估"):
        return "Escalate"
    if _has_any(text, "stop", "shutdown", "停机", "停止", "暂停", "停产", "急停"):
        return "Stop"
    if mode == "iqc":
        if _has_any(text, "scrap", "报废"):
            return "Scrap"
        if _has_any(text, "rework", "返工"):
            return "Rework"
        if _has_any(text, "hold", "quarantine", "隔离", "扣留", "冻结"):
            return "Hold"
        if _has_any(text, "expand", "扩大", "加严", "翻检"):
            return "Expand"
        if _has_any(text, "pass", "continue", "放行", "继续"):
            return "Continue"
        expected = IQC_DISPOSITION_ACTION_STARTERS.get((disposition or "").lower())
        if expected and _contains_cjk(action):
            return expected[0]
        return "Inspect" if _contains_cjk(action) else None
    if mode == "maintenance":
        if _has_any(text, "inspect", "check", "verify", "确认", "检查", "点检", "目视"):
            return "Inspect"
        if _has_any(text, "schedule", "plan", "安排", "计划", "窗口"):
            return "Schedule"
        if _has_any(text, "report", "notify", "记录", "报告", "通知"):
            return "Report"
        if _has_any(text, "monitor", "observe", "trend", "观察", "监控", "趋势"):
            return "Monitor"
        if _has_any(text, "keep", "continue", "保持", "继续"):
            return "Keep"
        return "Inspect" if _contains_cjk(action) else None
    if mode == "energy":
        if _has_any(text, "reduce", "降低", "减少", "节能", "削减"):
            return "Reduce"
        if _has_any(text, "shift", "错峰", "移峰", "转移"):
            return "Shift"
        if _has_any(text, "schedule", "安排", "计划", "窗口"):
            return "Schedule"
        if _has_any(text, "report", "记录", "报告", "通知"):
            return "Report"
        if _has_any(text, "hold", "保持暂停", "暂缓", "冻结"):
            return "Hold"
        if _has_any(text, "keep", "保持", "继续监测"):
            return "Keep"
        return "Inspect" if _contains_cjk(action) else None
    if mode == "changeover":
        if _has_any(text, "verify", "验证", "首件", "复核"):
            return "Verify"
        if _has_any(text, "set", "设定", "参数"):
            return "Set"
        if _has_any(text, "change", "更换", "转产", "切换"):
            return "Change"
        if _has_any(text, "hold", "隔离", "暂停"):
            return "Hold"
        if _has_any(text, "report", "报告", "通知"):
            return "Report"
        return "Confirm" if _contains_cjk(action) else None
    if mode == "wi":
        if _has_any(text, "ask", "询问", "请求"):
            return "Ask"
        if _has_any(text, "follow", "按照", "遵循", "执行"):
            return "Follow"
        if _has_any(text, "report", "报告", "通知"):
            return "Report"
        if _has_any(text, "keep", "保持", "维持"):
            return "Keep"
        return "Confirm" if _contains_cjk(action) else None
    if _has_any(text, "wear", "佩戴"):
        return "Wear"
    if _has_any(text, "report", "报告", "通知"):
        return "Report"
    if _has_any(text, "keep", "保持", "维持"):
        return "Keep"
    return "Inspect" if _contains_cjk(action) else None


def _has_any(text: str, *markers: str) -> bool:
    return any(marker in text for marker in markers)


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _already_contains_contract(prompt: str) -> bool:
    lowered = prompt.lower()
    return all(marker in lowered for marker in ("- scene:", "- risk:", "- action:", "do not add any introduction"))


def _already_contains_iqc_contract(prompt: str) -> bool:
    lowered = prompt.lower()
    return all(
        marker in lowered
        for marker in ("- product:", "- quality risk:", "- disposition:", "- action:", "do not add any introduction")
    )


def _already_contains_wi_contract(prompt: str) -> bool:
    lowered = prompt.lower()
    return all(marker in lowered for marker in ("- machine:", "- work instruction:", "- risk control:", "- action:"))


def _already_contains_changeover_contract(prompt: str) -> bool:
    lowered = prompt.lower()
    return all(
        marker in lowered
        for marker in ("- machine:", "- sku:", "- changeover step:", "- verification:", "- action:")
    )


def _already_contains_maintenance_contract(prompt: str) -> bool:
    lowered = prompt.lower()
    return all(
        marker in lowered
        for marker in ("- machine:", "- symptom:", "- maintenance risk:", "- evidence needed:", "- action:")
    )


def _already_contains_energy_contract(prompt: str) -> bool:
    lowered = prompt.lower()
    return all(
        marker in lowered
        for marker in ("- asset:", "- energy signal:", "- optimization:", "- verification:", "- action:")
    )


def _build_named_repair_prompt(name: str, contract_prompt: str, previous_answer: str) -> str:
    return (
        f"The previous answer did not satisfy the required {name} output contract. "
        "Use the image and rewrite the answer.\n\n"
        f"{contract_prompt}\n\n"
        "Do not use a code block. Do not add explanations.\n\n"
        "Previous answer:\n"
        f"{previous_answer.strip()}"
    )


def _normalize_contract_word_rule(prompt: str) -> str:
    normalized = re.sub(
        r"Each line must(?: be)? under 12 words\.",
        "Each line must be more than 15 words.",
        prompt,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(
        r"Each line must(?: be)? more than 15 words\.",
        "Each line must be more than 15 words.",
        normalized,
        flags=re.IGNORECASE,
    )
    return normalized
