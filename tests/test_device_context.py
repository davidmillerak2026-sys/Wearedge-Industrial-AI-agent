from __future__ import annotations

from jetson.device_context import DEFAULT_DEVICE_ID, MAX_FIELD_CHARS, build_device_context


def test_device_context_defaults_for_browser_demo() -> None:
    context = build_device_context(
        device_id=None,
        frame_ts=None,
        location_hint=None,
        capture_mode=None,
    )

    response = context.as_response()
    assert len(context.request_id) == 32
    assert context.received_at.endswith("Z")
    assert response["device"]["device_id"] == DEFAULT_DEVICE_ID
    assert response["device"]["frame_ts"] is None


def test_device_context_cleans_and_limits_fields() -> None:
    context = build_device_context(
        device_id="  M400\nUnit\t01  ",
        frame_ts=" device-generated-timestamp ",
        location_hint="A" * (MAX_FIELD_CHARS + 20),
        capture_mode=" camera-preview ",
    )

    assert context.device_id == "M400 Unit 01"
    assert context.frame_ts == "device-generated-timestamp"
    assert len(context.location_hint or "") == MAX_FIELD_CHARS
    assert context.capture_mode == "camera-preview"
