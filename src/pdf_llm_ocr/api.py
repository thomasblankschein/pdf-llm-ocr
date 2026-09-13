"""FastAPI-Service: POST /ocr nimmt ein PDF entgegen, liefert es mit
unsichtbarem, lagegetreuem Textlayer zurueck. Unter / liegt eine einfache
Test-Weboberflaeche (static/index.html)."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .config import load_settings
from .pipeline import run_ocr_pipeline

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

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
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY ist nicht gesetzt")

    result_bytes = run_ocr_pipeline(pdf_bytes, settings)
    return Response(content=result_bytes, media_type="application/pdf")


# Muss nach den API-Routen gemountet werden, da Starlette Routen in
# Registrierungsreihenfolge prueft - sonst wuerde der Catch-all-Mount
# frueher greifen als /health und /ocr.
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
