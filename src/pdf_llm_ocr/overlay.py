"""Baut den unsichtbaren Textlayer und legt ihn ueber die Original-PDF-Seiten.

Invisible-Text-Trick: PDF-Textrendermodus 3 ("Tr 3") zeichnet Text unsichtbar,
aber durchsuch-/kopierbar. reportlab hat dafuer keine oeffentliche API - das
ist derselbe Weg, den etablierte OCR-Layer-Tools (z.B. ocrmypdf's
hocrTransform) gehen: den Rendermodus per Rohkommando in den Content-Stream
schreiben.
"""

import io

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from .pdf_render import RenderedPage
from .tesseract_ocr import Word

_INVISIBLE_TEXT_RENDER_MODE = "3 Tr"


def _set_invisible_text_mode(pdf_canvas: canvas.Canvas) -> None:
    pdf_canvas._code.append(_INVISIBLE_TEXT_RENDER_MODE)


def build_overlay_page_pdf(page: RenderedPage, words: list[Word]) -> bytes:
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=(page.width_pt, page.height_pt))
    pdf_canvas.setFont("Helvetica", 1)
    _set_invisible_text_mode(pdf_canvas)

    px_to_pt = page.px_to_pt
    for word in words:
        if not word.text or word.width <= 0 or word.height <= 0:
            continue
        font_size = max(word.height * px_to_pt, 1.0)
        x_pt = word.left * px_to_pt
        # PDF-Ursprung ist unten links, Tesseract zaehlt Pixel von oben.
        y_pt = page.height_pt - (word.top + word.height) * px_to_pt

        pdf_canvas.setFont("Helvetica", font_size)
        text_object = pdf_canvas.beginText(x_pt, y_pt)
        text_width = pdf_canvas.stringWidth(word.text, "Helvetica", font_size)
        if text_width > 0:
            # Woerter horizontal auf die gemessene Tesseract-Box stauchen/strecken,
            # damit Suchmarkierungen ungefaehr passen (kein Layout-Rendering).
            scale = (word.width * px_to_pt) / text_width
            text_object.setHorizScale(scale * 100)
        text_object.textOut(word.text)
        pdf_canvas.drawText(text_object)

    pdf_canvas.save()
    return buffer.getvalue()


_FALLBACK_FONT_SIZE = 9
_FALLBACK_MARGIN_PT = 36  # 0.5 Zoll


def _wrap_line(pdf_canvas: canvas.Canvas, text: str, font_size: float, max_width: float) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or pdf_canvas.stringWidth(candidate, "Helvetica", font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def build_fallback_overlay_page_pdf(page: RenderedPage, text: str) -> bytes:
    """Wird verwendet, wenn Tesseract auf dieser Seite keine einzige Wort-Box
    liefern konnte (z.B. stark verblasste oder farbstichige Scans - siehe
    align.py). Ohne Tesseract-Boxen gibt es keine Positionen zum Ausrichten;
    damit die (oft trotzdem korrekte) LLM-Transkription nicht komplett
    verworfen wird, wird sie hier zeilenweise unsichtbar ueber die Seite gelegt
    - Lesereihenfolge bleibt erhalten, aber nicht lagegetreu zu einzelnen
    Woertern wie bei build_overlay_page_pdf."""
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=(page.width_pt, page.height_pt))
    pdf_canvas.setFont("Helvetica", _FALLBACK_FONT_SIZE)
    _set_invisible_text_mode(pdf_canvas)

    max_width = page.width_pt - 2 * _FALLBACK_MARGIN_PT
    line_height = _FALLBACK_FONT_SIZE * 1.3
    y = page.height_pt - _FALLBACK_MARGIN_PT

    for paragraph in text.splitlines():
        for line in _wrap_line(pdf_canvas, paragraph, _FALLBACK_FONT_SIZE, max_width):
            if y < _FALLBACK_MARGIN_PT:
                pdf_canvas.save()
                return buffer.getvalue()
            pdf_canvas.drawString(_FALLBACK_MARGIN_PT, y, line)
            y -= line_height

    pdf_canvas.save()
    return buffer.getvalue()


def merge_text_layer(original_pdf_bytes: bytes, overlay_pages: list[bytes]) -> bytes:
    reader = PdfReader(io.BytesIO(original_pdf_bytes))
    writer = PdfWriter()

    for index, page in enumerate(reader.pages):
        if index < len(overlay_pages):
            overlay_reader = PdfReader(io.BytesIO(overlay_pages[index]))
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
