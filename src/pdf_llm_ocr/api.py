"""FastAPI-Service: POST /ocr nimmt ein PDF entgegen, liefert es mit
unsichtbarem, lagegetreuem Textlayer zurueck."""

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import Response

from .config import load_settings
from .pipeline import run_ocr_pipeline

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
