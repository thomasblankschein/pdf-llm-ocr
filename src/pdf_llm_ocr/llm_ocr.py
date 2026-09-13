"""Ruft ein Vision-LLM fuer hochwertige Text-Transkription einer Seite auf.

Analog zu paperless-gpt's ocr_prompt.tmpl: die vorhandene (Tesseract-)
Rohtranskription wird als Referenz mitgegeben, damit das LLM schwierige
Woerter/Zahlen einordnen kann, sich aber primaer auf das Bild verlaesst.
"""

import base64
import io
from pathlib import Path

import anthropic
from PIL import Image

_PROMPT_TEMPLATE = (Path(__file__).parent.parent.parent / "prompts" / "ocr_prompt.txt").read_text(
    encoding="utf-8"
)


def _build_prompt(reference_text: str, max_reference_chars: int) -> str:
    reference_text = reference_text.strip()
    if len(reference_text) > max_reference_chars:
        reference_text = reference_text[:max_reference_chars]
    reference_block = ""
    if reference_text:
        reference_block = (
            "Fuer diese Seite liegt bereits eine grobe OCR-Rohtranskription vor. "
            "Nutze sie nur, um schwer lesbare Woerter oder Zahlen einzuordnen; "
            "verlasse dich primaer auf das Bild und korrigiere Fehler:\n\n"
            f"{reference_text}"
        )
    return _PROMPT_TEMPLATE.format(reference_block=reference_block)


def _image_to_base64_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.standard_b64encode(buffer.getvalue()).decode("ascii")


def transcribe_page(
    client: anthropic.Anthropic,
    model: str,
    image: Image.Image,
    reference_text: str,
    max_reference_chars: int,
) -> str:
    prompt = _build_prompt(reference_text, max_reference_chars)
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
                            "data": _image_to_base64_png(image),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
