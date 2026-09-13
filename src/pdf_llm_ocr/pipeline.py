"""Orchestriert den gesamten Ablauf: PDF rein, PDF mit Textlayer raus."""

from . import align, llm_provider, overlay, tesseract_ocr
from .config import Settings
from .pdf_render import render_pages


def run_ocr_pipeline(pdf_bytes: bytes, settings: Settings) -> bytes:
    pages = render_pages(pdf_bytes, dpi=settings.render_dpi)
    provider = llm_provider.create_provider(settings)

    overlay_pages: list[bytes] = []
    for page in pages:
        tesseract_words = tesseract_ocr.extract_words(page.image, lang=settings.tesseract_lang)
        reference_text = " ".join(word.text for word in tesseract_words)

        corrected_text = provider.transcribe(
            client=provider.client,
            model=provider.model,
            image=page.image,
            reference_text=reference_text,
            max_reference_chars=settings.max_reference_chars,
        )

        result = align.align_words_to_boxes(tesseract_words, corrected_text)
        if result.coverage >= settings.min_alignment_coverage:
            overlay_pages.append(overlay.build_overlay_page_pdf(page, result.words))
        else:
            # Zu wenige (oder gar keine) Tesseract-Boxen konnten dem LLM-Text
            # zugeordnet werden (z.B. stark verblasste/farbstichige Scans) -
            # der grossteil wuerde in align.py als "insert" verworfen. Stattdessen
            # den LLM-Text ohne Wort-Positionen ablegen, damit er wenigstens
            # vollstaendig durchsuchbar bleibt statt still verstuemmelt zu werden.
            overlay_pages.append(overlay.build_fallback_overlay_page_pdf(page, corrected_text))

    return overlay.merge_text_layer(pdf_bytes, overlay_pages)
