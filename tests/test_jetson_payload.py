from __future__ import annotations

import base64

from jetson.llama_client import build_multimodal_payload


def test_multimodal_payload_contains_data_url_image() -> None:
    payload = build_multimodal_payload(
        prompt="Describe this frame.",
        image_bytes=b"fake-jpeg",
        image_content_type="image/jpeg",
        model="gemma4",
        enable_thinking=True,
        max_tokens=64,
        temperature=0.2,
    )

    content = payload["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "Describe this frame."}
    image_url = content[1]["image_url"]["url"]
    assert image_url.startswith("data:image/jpeg;base64,")
    encoded = image_url.split(",", 1)[1]
    assert base64.b64decode(encoded) == b"fake-jpeg"
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}
