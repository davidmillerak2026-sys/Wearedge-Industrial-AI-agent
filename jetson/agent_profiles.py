from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentProfile:
    mode: str
    display_name: str
    purpose: str
    aliases: tuple[str, ...] = ()


AGENT_PROFILES: dict[str, AgentProfile] = {
    "maintenance": AgentProfile(
        mode="maintenance",
        display_name="lao-shi-fu predictive maintenance",
        purpose="Preserve experienced maintenance know-how and guide bounded machine risk investigation.",
        aliases=("lao_shi_fu", "laos_shi_fu", "predictive_maintenance", "pm", "maintenance_agent"),
    ),
    "iqc": AgentProfile(
        mode="iqc",
        display_name="IQC online quality inspection",
        purpose="Identify visible in-process product quality risk and containment disposition.",
        aliases=("quality", "inspection", "quality_inspection", "product_quality", "quality_agent", "iqc_agent"),
    ),
    "energy": AgentProfile(
        mode="energy",
        display_name="energy management",
        purpose="Evaluate energy usage, idle load, peak demand, and bounded optimization recommendations.",
        aliases=("energy_management", "energy_agent", "power", "power_management", "carbon", "zero_carbon"),
    ),
    "changeover": AgentProfile(
        mode="changeover",
        display_name="changeover guidance",
        purpose="Guide controlled SKU or recipe changeover from visible machine and product context.",
        aliases=("sku_changeover", "model_changeover", "turnover", "changeover_agent"),
    ),
    "wi": AgentProfile(
        mode="wi",
        display_name="general work instruction",
        purpose="Answer operator machine-use questions with bounded work-instruction guidance.",
        aliases=("work_instruction", "work_instructions", "instruction", "general_wi", "wi_agent"),
    ),
    "hazard": AgentProfile(
        mode="hazard",
        display_name="hazard exposure",
        purpose="Identify production-area safety exposure and safe next action.",
        aliases=("safety", "hazard_exposure", "ehs", "risk", "safety_agent"),
    ),
}

ALIASES: dict[str, str] = {
    alias: mode
    for mode, profile in AGENT_PROFILES.items()
    for alias in (mode, *profile.aliases)
}


def normalize_agent_mode(value: str | None) -> str:
    normalized = (value or "hazard").strip().lower().replace("-", "_")
    return ALIASES.get(normalized, normalized)
