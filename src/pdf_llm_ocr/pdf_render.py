"""Rendert PDF-Seiten als Bilder fuer OCR, bei bekannter Seitengroesse in PDF-Punkten."""

from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image


@dataclass
class RenderedPage:
    index: int
    image: Image.Image
    dpi: int
    width_pt: float
    height_pt: float

    @property
    def px_to_pt(self) -> float:
        return 72.0 / self.dpi


def render_pages(pdf_bytes: bytes, dpi: int) -> list[RenderedPage]:
    pages: list[RenderedPage] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        for index, page in enumerate(doc):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            pages.append(
                RenderedPage(
                    index=index,
                    image=image,
                    dpi=dpi,
                    width_pt=page.rect.width,
                    height_pt=page.rect.height,
                )
            )
    finally:
        doc.close()
    return pages
