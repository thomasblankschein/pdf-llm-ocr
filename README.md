# pdf-llm-ocr

Service, der ein PDF entgegennimmt, eine Vision-LLM-OCR durchfuehrt und das
Ergebnis als lagegetreuen, unsichtbaren Textlayer in das PDF zurueckschreibt
(durchsuchbar/kopierbar, visuell unveraendert).

## Architektur

Ein Vision-LLM liefert zuverlaessig guten **Text**, aber keine pixelgenauen
**Positionen**. Ein lagegetreuer Textlayer (wie ihn `ocrmypdf` mit Tesseract
baut) braucht aber genau das: eine Bounding-Box pro Wort. Deshalb ein
Hybrid-Ansatz:

```
PDF rein
  -> pro Seite als Bild rendern (PyMuPDF, konfigurierbares DPI)
  -> Tesseract liefert Wort-Bounding-Boxes (Position, aber mittelmaessige Texttreue)
  -> Seitenbild + Tesseract-Text als Referenz an ein Vision-LLM (Claude)
     -> LLM liefert korrigierten Fliesstext (Texttreue, aber ohne Positionen)
  -> Tesseract-Woerter und LLM-Text per Sequence-Alignment (difflib) verheiraten
  -> unsichtbaren Textlayer (PDF-Rendermodus "3 Tr") an Tesseract-Positionen
     mit LLM-korrigiertem Text bauen
  -> Layer ueber die Original-Seite legen (Originalinhalt bleibt unveraendert sichtbar)
PDF raus
```

Warum Tesseract fuer Positionen: Es ist die etablierte, verlaessliche Quelle
fuer Wort-Bounding-Boxes. Vision-LLMs koennen zwar nach Koordinaten gefragt
werden, driften bei dichtem Text oder mehrspaltigem Layout aber sichtbar.
Das LLM wird hier ausschliesslich fuer Textqualitaet eingesetzt, nicht fuer
Geometrie.

## Module (`src/pdf_llm_ocr/`)

| Datei | Aufgabe |
|---|---|
| `pdf_render.py` | PDF-Seiten als Bilder rendern (PyMuPDF), Seitenmasse in PDF-Punkten |
| `tesseract_ocr.py` | Wort-Bounding-Boxes per Tesseract (`pytesseract.image_to_data`) |
| `llm_ocr.py` | Vision-LLM-Aufruf (Anthropic) mit Tesseract-Text als Referenz |
| `align.py` | Sequence-Alignment: LLM-Text auf Tesseract-Boxen abbilden |
| `overlay.py` | Unsichtbaren Textlayer bauen (reportlab) und mergen (pypdf) |
| `pipeline.py` | Orchestriert obige Schritte pro Dokument |
| `api.py` | FastAPI-Endpoint `POST /ocr` |

## Setup

Systemvoraussetzung: **Tesseract** muss installiert sein (inkl. gewuenschter
Sprachpakete, Standard hier `deu+eng`).

```bash
pip install -e ".[dev]"
cp .env.example .env   # ANTHROPIC_API_KEY eintragen
```

## Starten

```bash
uvicorn pdf_llm_ocr.api:app --reload --app-dir src
```

```bash
curl -X POST http://localhost:8000/ocr -F "file=@input.pdf" -o output.pdf
```

## Tests

```bash
PYTHONPATH=src pytest
```

Aktuell nur Unit-Tests fuer die Alignment-Logik (`tests/test_align.py`) –
keine externen Abhaengigkeiten (kein Tesseract-Binary, kein API-Key) noetig.

## Bekannte Grenzen / naechste Schritte

- **Alignment-Heuristik ist bewusst einfach** (siehe Docstring in `align.py`):
  Woerter, die das LLM zusaetzlich erkennt, aber die Tesseract nicht sah,
  haben keine Box und werden verworfen. Bei ungleich langen Ersetzungsbloecken
  werden ueberzaehlige Tesseract-Woerter unveraendert uebernommen.
- **Kein Zeilenumbruch-/Absatz-Handling**: Der Textlayer besteht aus
  einzelnen Woerter-Boxen, keine zusammenhaengenden Textbloecke.
- **Kein Caching/Queueing**: Jede Anfrage laeuft synchron; fuer groessere
  PDFs oder hohen Durchsatz braucht es eine Job-Queue.
- **Keine Auth**: Der Endpoint ist unauthentifiziert, fuer den produktiven
  Einsatz noetig nachzuruesten.
- Noch nicht End-to-End getestet (Tesseract-Binary/Anthropic-Key nicht in
  jeder Umgebung verfuegbar) – die Alignment-Logik ist isoliert getestet,
  der volle Pfad (Rendern -> Tesseract -> LLM -> Merge) sollte vor
  produktivem Einsatz einmal manuell durchlaufen werden.
