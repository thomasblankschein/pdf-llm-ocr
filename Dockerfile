FROM python:3.12-slim

# tesseract-ocr wird hier ins Image gebacken statt eine Host-Installation
# vorauszusetzen - das ist der Grund, warum das Image auf jeder Docker-
# faehigen Plattform ohne weitere Vorbereitung laeuft. Sprachpakete passend
# zum Standard-Env "deu+eng" (PDF_LLM_OCR_TESS_LANG); weitere per
# tesseract-ocr-<code> ergaenzen, falls andere Sprachen gebraucht werden.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "pdf_llm_ocr.api:app", "--host", "0.0.0.0", "--port", "8000"]
