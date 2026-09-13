"""Orchestriert den gesamten Ablauf: PDF rein, PDF mit Textlayer raus."""

import anthropic

from . import align, llm_ocr, overlay, tesseract_ocr
from .config import Settings
from .pdf_render import render_pages


def run_ocr_pipeline(pdf_bytes: bytes, settings: Settings) -> bytes:
    pages = render_pages(pdf_bytes, dpi=settings.render_dpi)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    overlay_pages: list[bytes] = []
    for page in pages:
        tesseract_words = tesseract_ocr.extract_words(page.image, lang=settings.tesseract_lang)
        reference_text = " ".join(word.text for word in tesseract_words)

        corrected_text = llm_ocr.transcribe_page(
            client=client,
            model=settings.anthropic_model,
            image=page.image,
            reference_text=reference_text,
            max_reference_chars=settings.max_reference_chars,
        )

        positioned_words = align.align_words_to_boxes(tesseract_words, corrected_text)
        overlay_pages.append(overlay.build_overlay_page_pdf(page, positioned_words))

    return overlay.merge_text_layer(pdf_bytes, overlay_pages)
