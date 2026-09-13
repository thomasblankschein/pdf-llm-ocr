"""Ruft Claude (Anthropic) fuer hochwertige Text-Transkription einer Seite auf."""

import anthropic
from PIL import Image

from .image_utils import image_to_base64_png
from .prompt import build_prompt


def transcribe_page(
    client: anthropic.Anthropic,
    model: str,
    image: Image.Image,
    reference_text: str,
    max_reference_chars: int,
) -> str:
    prompt = build_prompt(reference_text, max_reference_chars)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_to_base64_png(image),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
