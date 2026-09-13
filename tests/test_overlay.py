from pdf_llm_ocr.overlay import build_fallback_overlay_page_pdf
from pdf_llm_ocr.pdf_render import RenderedPage
from PIL import Image


def _blank_page() -> RenderedPage:
    return RenderedPage(index=0, image=Image.new("RGB", (10, 10)), dpi=300, width_pt=595, height_pt=842)


def test_fallback_overlay_produces_valid_pdf_bytes():
    pdf_bytes = build_fallback_overlay_page_pdf(_blank_page(), "Hallo Welt\nZweite Zeile")
    assert pdf_bytes.startswith(b"%PDF")


def test_fallback_overlay_handles_long_text_without_crashing():
    long_text = "\n".join(f"Zeile {i} mit etwas mehr Text zum Umbrechen" for i in range(200))
    pdf_bytes = build_fallback_overlay_page_pdf(_blank_page(), long_text)
    assert pdf_bytes.startswith(b"%PDF")


def test_fallback_overlay_handles_empty_text():
    pdf_bytes = build_fallback_overlay_page_pdf(_blank_page(), "")
    assert pdf_bytes.startswith(b"%PDF")
