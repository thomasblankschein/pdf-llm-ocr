"""FastAPI-Service: POST /ocr nimmt ein PDF entgegen, liefert es mit
unsichtbarem, lagegetreuem Textlayer zurueck. Unter / liegt eine einfache
Test-Weboberflaeche (static/index.html)."""

import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

from . import llm_provider
from .config import load_settings
from .pipeline import run_ocr_pipeline

_STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="pdf-llm-ocr")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ocr")
async def ocr(file: UploadFile) -> Response:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Erwarte application/pdf")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Leere Datei")

    settings = load_settings()
    if settings.llm_provider not in llm_provider.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=500,
            detail=f"Unbekannter PDF_LLM_OCR_PROVIDER '{settings.llm_provider}'"
            f" - erwartet einen von {llm_provider.SUPPORTED_PROVIDERS}",
        )
    if not llm_provider.api_key_for(settings):
        raise HTTPException(
            status_code=500,
            detail=f"API-Key fuer Provider '{settings.llm_provider}' ist nicht gesetzt",
        )

    result_bytes = run_ocr_pipeline(pdf_bytes, settings)
    return Response(content=result_bytes, media_type="application/pdf")


@app.post("/extract-text")
async def extract_text(file: UploadFile) -> dict[str, str]:
    """Liest den in einem PDF eingebetteten Text aus (fuer die Test-Weboberflaeche:
    zeigt, was von einem OCR-Ergebnis-PDF tatsaechlich durchsuchbar/kopierbar ist).
    Fuehrt selbst keine OCR durch, nur eine reine Textextraktion via pypdf."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Erwarte application/pdf")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Leere Datei")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return {"text": text}


# Muss nach den API-Routen gemountet werden, da Starlette Routen in
# Registrierungsreihenfolge prueft - sonst wuerde der Catch-all-Mount
# frueher greifen als /health und /ocr.
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
