from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


DEFAULT_DEVICE_ID = "web-demo"
MAX_FIELD_CHARS = 120
_SPACE_RE = re.compile(r"\s+")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class DeviceContext:
    request_id: str
    received_at: str
    device_id: str
    frame_ts: str | None
    location_hint: str | None
    capture_mode: str | None

    def as_response(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "received_at": self.received_at,
            "device": {
                "device_id": self.device_id,
                "frame_ts": self.frame_ts,
                "location_hint": self.location_hint,
                "capture_mode": self.capture_mode,
            },
        }


def build_device_context(
    *,
    device_id: str | None,
    frame_ts: str | None,
    location_hint: str | None,
    capture_mode: str | None,
) -> DeviceContext:
    return DeviceContext(
        request_id=uuid.uuid4().hex,
        received_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        device_id=_clean_field(device_id, default=DEFAULT_DEVICE_ID) or DEFAULT_DEVICE_ID,
        frame_ts=_clean_field(frame_ts),
        location_hint=_clean_field(location_hint),
        capture_mode=_clean_field(capture_mode),
    )


def _clean_field(value: str | None, *, default: str | None = None) -> str | None:
    if value is None:
        return default
    cleaned = _CONTROL_RE.sub(" ", value)
    cleaned = _SPACE_RE.sub(" ", cleaned).strip()
    if not cleaned:
        return default
    return cleaned[:MAX_FIELD_CHARS]
