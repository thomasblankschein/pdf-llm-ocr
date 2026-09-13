"""Liefert Wort-Bounding-Boxes per Tesseract - die Positionsquelle fuer den Textlayer.

Das LLM liefert spaeter nur noch bessere Textqualitaet; die Position jedes
Wortes kommt von hier, weil Vision-LLMs keine verlaesslich pixelgenauen
Koordinaten liefern (siehe README, Abschnitt "Warum Tesseract fuer Positionen").
"""

from dataclasses import dataclass

import pytesseract
from PIL import Image
from pytesseract import Output


@dataclass
class Word:
    text: str
    left: int
    top: int
    width: int
    height: int


def extract_words(image: Image.Image, lang: str, min_confidence: int = 0) -> list[Word]:
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT)
    words: list[Word] = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text:
            continue
        try:
            confidence = int(float(data["conf"][i]))
        except (ValueError, IndexError):
            confidence = -1
        if confidence < min_confidence:
            continue
        words.append(
            Word(
                text=text,
                left=data["left"][i],
                top=data["top"][i],
                width=data["width"][i],
                height=data["height"][i],
            )
        )
    return words
