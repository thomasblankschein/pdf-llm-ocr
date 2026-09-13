"""Zentrale Konfiguration, aus Umgebungsvariablen gelesen."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    anthropic_api_key: str
    anthropic_model: str
    openai_api_key: str
    openai_model: str
    render_dpi: int
    tesseract_lang: str
    max_reference_chars: int
    min_alignment_coverage: float


def load_settings() -> Settings:
    return Settings(
        llm_provider=os.environ.get("PDF_LLM_OCR_PROVIDER", "anthropic").strip().lower(),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.environ.get("PDF_LLM_OCR_MODEL", "claude-sonnet-5"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_model=os.environ.get("PDF_LLM_OCR_OPENAI_MODEL", "gpt-5.5"),
        render_dpi=int(os.environ.get("PDF_LLM_OCR_DPI", "300")),
        tesseract_lang=os.environ.get("PDF_LLM_OCR_TESS_LANG", "deu+eng"),
        max_reference_chars=int(os.environ.get("PDF_LLM_OCR_MAX_REF_CHARS", "8000")),
        min_alignment_coverage=float(os.environ.get("PDF_LLM_OCR_MIN_ALIGNMENT_COVERAGE", "0.5")),
    )
