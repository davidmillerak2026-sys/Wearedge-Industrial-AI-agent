from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


TRUE_VALUES = {"1", "true", "yes", "on"}


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


@dataclass(frozen=True)
class GatewayConfig:
    llama_base_url: str
    model: str
    demo_token: str | None
    max_image_mb: int
    enable_thinking: bool
    max_tokens: int
    temperature: float
    timeout_seconds: int
    upload_dir: Path | None
    event_log_path: Path | None
    auth_disabled: bool
    contract_min_words: int
    contract_repair_enabled: bool
    llama_image_min_tokens: int
    llama_image_max_tokens: int
    audio_fusion_runtime: str
    model_variant: str
    xcelerator_x_auth_enabled: bool = False
    xcelerator_app_key: str | None = None
    xcelerator_sign_check_url: str = "https://apig.developers.siemens-x.com.cn/x-api/sign/check"
    xcelerator_sign_check_timeout_seconds: int = 10

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        upload_dir_value = os.getenv("WEAREDGE_UPLOAD_DIR")
        event_log_value = os.getenv("WEAREDGE_EVENT_LOG")
        return cls(
            llama_base_url=os.getenv("LLAMA_BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
            model=os.getenv("LLAMA_MODEL", "gemma4"),
            demo_token=os.getenv("DEMO_TOKEN"),
            max_image_mb=_int_env("WEAREDGE_MAX_IMAGE_MB", 4),
            enable_thinking=_bool_env("WEAREDGE_ENABLE_THINKING", True),
            max_tokens=_int_env("WEAREDGE_MAX_TOKENS", 160),
            temperature=_float_env("WEAREDGE_TEMPERATURE", 0.2),
            timeout_seconds=_int_env("WEAREDGE_TIMEOUT_SECONDS", 120),
            upload_dir=Path(upload_dir_value) if upload_dir_value else None,
            event_log_path=Path(event_log_value) if event_log_value else None,
            auth_disabled=_bool_env("WEAREDGE_AUTH_DISABLED", False),
            contract_min_words=_int_env("WEAREDGE_CONTRACT_MIN_WORDS", 16),
            contract_repair_enabled=_bool_env("WEAREDGE_CONTRACT_REPAIR_ENABLED", True),
            llama_image_min_tokens=_int_env("LLAMA_IMAGE_MIN_TOKENS", 70),
            llama_image_max_tokens=_int_env("LLAMA_IMAGE_MAX_TOKENS", 70),
            audio_fusion_runtime=os.getenv("WEAREDGE_AUDIO_FUSION_RUNTIME", "llama.cpp"),
            model_variant=os.getenv("WEAREDGE_MODEL_VARIANT", "E2B"),
            xcelerator_x_auth_enabled=_bool_env("WEAREDGE_XCELERATOR_X_AUTH_ENABLED", False),
            xcelerator_app_key=os.getenv("WEAREDGE_XCELERATOR_APP_KEY"),
            xcelerator_sign_check_url=os.getenv(
                "WEAREDGE_XCELERATOR_SIGN_CHECK_URL",
                "https://apig.developers.siemens-x.com.cn/x-api/sign/check",
            ),
            xcelerator_sign_check_timeout_seconds=_int_env("WEAREDGE_XCELERATOR_SIGN_CHECK_TIMEOUT_SECONDS", 10),
        )

    @property
    def auth_enabled(self) -> bool:
        return not self.auth_disabled
