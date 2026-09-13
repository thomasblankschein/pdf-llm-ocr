"""Ruft ein OpenAI-Vision-Modell fuer hochwertige Text-Transkription einer Seite auf.

Analog zu llm_ocr.py (Claude), nur mit der OpenAI Chat-Completions-API statt
der Anthropic Messages-API. `max_completion_tokens` statt des mittlerweile
fuer neuere Modelle als veraltet markierten `max_tokens` - siehe
OpenAI-API-Referenz zu chat.completions.create.
"""

import openai
from PIL import Image

from .image_utils import image_to_base64_png
from .prompt import build_prompt


def transcribe_page(
    client: openai.OpenAI,
    model: str,
    image: Image.Image,
    reference_text: str,
    max_reference_chars: int,
) -> str:
    prompt = build_prompt(reference_text, max_reference_chars)
    data_url = f"data:image/png;base64,{image_to_base64_png(image)}"
    response = client.chat.completions.create(
        model=model,
        max_completion_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return (response.choices[0].message.content or "").strip()
