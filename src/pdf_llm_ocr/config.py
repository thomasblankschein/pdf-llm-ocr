"""Zentrale Konfiguration, aus Umgebungsvariablen gelesen."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    anthropic_model: str
    render_dpi: int
    tesseract_lang: str
    max_reference_chars: int


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.environ.get("PDF_LLM_OCR_MODEL", "claude-sonnet-5"),
        render_dpi=int(os.environ.get("PDF_LLM_OCR_DPI", "300")),
        tesseract_lang=os.environ.get("PDF_LLM_OCR_TESS_LANG", "deu+eng"),
        max_reference_chars=int(os.environ.get("PDF_LLM_OCR_MAX_REF_CHARS", "8000")),
    )
