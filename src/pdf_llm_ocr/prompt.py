"""Baut den OCR-Prompt - provider-unabhaengig, von jedem llm_ocr_*.py genutzt.

Analog zu paperless-gpt's ocr_prompt.tmpl: die vorhandene (Tesseract-)
Rohtranskription wird als Referenz mitgegeben, damit das LLM schwierige
Woerter/Zahlen einordnen kann, sich aber primaer auf das Bild verlaesst.
"""

from pathlib import Path

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "ocr_prompt.txt").read_text(encoding="utf-8")


def build_prompt(reference_text: str, max_reference_chars: int) -> str:
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
