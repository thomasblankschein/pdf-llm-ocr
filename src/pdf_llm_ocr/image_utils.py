"""Bild-Hilfsfunktionen, die von allen LLM-Providern gleich gebraucht werden."""

import base64
import io

from PIL import Image


def image_to_base64_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.standard_b64encode(buffer.getvalue()).decode("ascii")
