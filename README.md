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
  -> Seitenbild + Tesseract-Text als Referenz an ein Vision-LLM (Claude oder OpenAI)
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
| `prompt.py` | Baut den (provider-unabhaengigen) OCR-Prompt inkl. Tesseract-Referenztext |
| `image_utils.py` | Bild-zu-Base64-PNG-Encoding, von beiden Providern genutzt |
| `llm_ocr.py` | Vision-LLM-Aufruf gegen Claude (Anthropic Messages API) |
| `llm_ocr_openai.py` | Vision-LLM-Aufruf gegen OpenAI (Chat Completions API) - identische Signatur wie `llm_ocr.py` |
| `llm_provider.py` | Waehlt anhand `PDF_LLM_OCR_PROVIDER` zwischen beiden Providern, baut den passenden Client |
| `align.py` | Sequence-Alignment: LLM-Text auf Tesseract-Boxen abbilden |
| `overlay.py` | Unsichtbaren Textlayer bauen (reportlab) und mergen (pypdf); Fallback ohne Wort-Positionen, wenn Tesseract 0 Woerter fand |
| `pipeline.py` | Orchestriert obige Schritte pro Dokument |
| `api.py` | FastAPI-Endpoints `POST /ocr` und `POST /extract-text`, mountet `static/` als Test-Weboberflaeche |

`POST /extract-text` fuehrt keine OCR durch, sondern liest per `pypdf` nur den
in einem hochgeladenen PDF bereits eingebetteten Text aus (`{"text": "..."}`).
Dient der Weboberflaeche dazu, nach einem `/ocr`-Lauf direkt zu zeigen, was im
Ergebnis-PDF tatsaechlich durchsuchbar/kopierbar ist.

`prompts/` und `static/` liegen bewusst *innerhalb* von `src/pdf_llm_ocr/`
(nicht auf Projekt-Root-Ebene) und sind in `pyproject.toml` als Package-Data
deklariert – nur so landen sie auch in einer regulaeren (nicht-editierbaren)
Installation, wie sie das `Dockerfile` durchfuehrt. `static/index.html` ist
eine eigenstaendige HTML/JS-Seite (kein Build-Schritt, keine externen
Abhaengigkeiten) zum manuellen Ausprobieren des Endpoints.

## LLM-Provider waehlen

`PDF_LLM_OCR_PROVIDER` schaltet zwischen zwei austauschbaren Vision-LLM-
Implementierungen um, ohne dass sich sonst etwas am Ablauf aendert (Tesseract-
Positionen, Alignment, Textlayer-Bau sind provider-unabhaengig):

| `PDF_LLM_OCR_PROVIDER` | Benoetigter Key | Modell-Env-Var | Default-Modell |
|---|---|---|---|
| `anthropic` (Default) | `ANTHROPIC_API_KEY` | `PDF_LLM_OCR_MODEL` | `claude-sonnet-5` |
| `openai` | `OPENAI_API_KEY` | `PDF_LLM_OCR_OPENAI_MODEL` | `gpt-5.5` |

Nur der Key des jeweils aktiven Providers wird gebraucht; `/ocr` liefert einen
klaren 500er (`API-Key fuer Provider '...' ist nicht gesetzt`), falls er fehlt.
Beide Implementierungen (`llm_ocr.py` fuer Claude, `llm_ocr_openai.py` fuer
OpenAI) teilen sich Prompt-Aufbau (`prompt.py`) und Bild-Encoding
(`image_utils.py`) – `llm_provider.py` waehlt anhand der Config nur noch den
passenden Client und die passende `transcribe_page`-Funktion aus.

**Das OpenAI-Default-Modell `gpt-5.5` ist nicht selbst getestet** (siehe
"Bekannte Grenzen") – OpenAIs Modell-Namensschema aendert sich haeufig, dieser
Wert kann bei dir bereits veraltet sein. Vor dem produktiven Einsatz gegen
OpenAIs aktuelle Modellliste pruefen und `PDF_LLM_OCR_OPENAI_MODEL` bei Bedarf
anpassen – keine Codeaenderung noetig.

## Betrieb per Docker (empfohlen)

Einzige Voraussetzung: Docker mit Compose-Plugin. Tesseract wird beim
Image-Build automatisch mitinstalliert (siehe `Dockerfile`) – es muss auf dem
Zielsystem nichts manuell eingerichtet werden, egal welche Plattform Docker
dort betreibt.

```bash
cp .env.example .env   # ANTHROPIC_API_KEY eintragen
docker compose up -d --build
```

Danach: Test-Weboberflaeche unter [http://localhost:8000](http://localhost:8000),
Endpoint unter `http://localhost:8000/ocr`. Ein Healthcheck (`GET /health`) ist
in `docker-compose.yml` hinterlegt.

Weitere Sprachen fuer Tesseract: im `Dockerfile` bei den `tesseract-ocr-<code>`-
Paketen ergaenzen und `PDF_LLM_OCR_TESS_LANG` in `.env` entsprechend setzen
(Paketnamen und Sprachcodes muessen zusammenpassen, z.B. `tesseract-ocr-fra`
fuer `fra`).

## Lokale Entwicklung ohne Docker

Systemvoraussetzung: **Tesseract** muss lokal installiert sein (inkl.
gewuenschter Sprachpakete, Standard hier `deu+eng`) – das ersetzt der
Docker-Weg oben.

```bash
pip install -e ".[dev]"
cp .env.example .env   # ANTHROPIC_API_KEY eintragen
uvicorn pdf_llm_ocr.api:app --reload --app-dir src
```

Test-Weboberflaeche: [http://localhost:8000](http://localhost:8000) – PDF hochladen,
Ergebnis wird nach Verarbeitung inline angezeigt, ist herunterladbar, und der
darin enthaltene Text wird zusaetzlich in einem groessenverstellbaren
Textfeld angezeigt (`static/index.html`, ruft `POST /ocr` und danach
`POST /extract-text` auf).

Oder direkt per curl:

```bash
curl -X POST http://localhost:8000/ocr -F "file=@input.pdf" -o output.pdf
```

## Tests

```bash
PYTHONPATH=src pytest
```

Aktuell Unit-Tests fuer die Alignment-Logik (`tests/test_align.py`) und den
Fallback-Textlayer (`tests/test_overlay.py`) – keine externen Abhaengigkeiten
(kein Tesseract-Binary, kein API-Key) noetig.

## Bekannte Grenzen / naechste Schritte

- **Alignment-Heuristik ist bewusst einfach** (siehe Docstring in `align.py`):
  Woerter, die das LLM zusaetzlich erkennt, aber die Tesseract nicht sah,
  haben keine Box und werden verworfen. Bei ungleich langen Ersetzungsbloecken
  werden ueberzaehlige Tesseract-Woerter unveraendert uebernommen. Findet
  Tesseract auf einer Seite zu wenige Boxen (bis hin zu gar keinen – z.B.
  stark verblasste oder farbstichige Scans, in der Praxis beobachtet an einem
  Kassenbon-Scan), wuerde das den Grossteil des LLM-Texts als "insert"
  verwerfen. `align_words_to_boxes` gibt dafuer `coverage` zurueck (Anteil der
  LLM-Woerter, die tatsaechlich eine Position bekommen haben); faellt dieser
  Wert unter `PDF_LLM_OCR_MIN_ALIGNMENT_COVERAGE` (Default `0.5`), verwendet
  `pipeline.py` statt der Wort-Positionen `overlay.build_fallback_overlay_page_pdf`:
  der LLM-Text wird zeilenweise ohne Wort-Position abgelegt, damit er
  wenigstens vollstaendig durchsuchbar bleibt, statt zu grossen Teilen still
  zu verschwinden. Der Schwellwert ist eine Heuristik, keine empirisch
  hergeleitete Zahl - bei Bedarf per Env-Var justierbar.
- **Kein Zeilenumbruch-/Absatz-Handling**: Der Textlayer besteht aus
  einzelnen Woerter-Boxen, keine zusammenhaengenden Textbloecke.
- **OpenAI-Pfad ist nicht end-to-end getestet** – kein OpenAI-API-Key in dieser
  Entwicklungsumgebung verfuegbar. Verifiziert wurde: Provider-Auswahl per
  `PDF_LLM_OCR_PROVIDER` (Unit-Tests in `tests/test_llm_provider.py`), der
  Fehlerpfad bei fehlendem `OPENAI_API_KEY` (echter 500er gegen den laufenden
  Container), und dass der Anthropic-Pfad nach dem Umbau auf die gemeinsame
  Provider-Abstraktion weiterhin unveraendert funktioniert (Regressionstest
  mit echtem OCR-Aufruf). Nicht verifiziert: ein tatsaechlicher
  `/ocr`-Durchlauf mit `PDF_LLM_OCR_PROVIDER=openai` und echtem Key - das
  exakte Request-Format (`image_url`-Content-Block, `max_completion_tokens`)
  stammt aus der aktuellen OpenAI-API-Referenz, nicht aus einem eigenen Test.
  Das Default-Modell `gpt-5.5` ebenfalls unverifiziert, siehe Abschnitt
  "LLM-Provider waehlen".
- **Kein Caching/Queueing**: Jede Anfrage laeuft synchron; fuer groessere
  PDFs oder hohen Durchsatz braucht es eine Job-Queue.
- **Keine Auth**: Der Endpoint ist unauthentifiziert, fuer den produktiven
  Einsatz noetig nachzuruesten.
- **Der volle Erfolgspfad (Rendern -> Tesseract -> LLM -> Merge) ist noch
  nicht End-to-End mit einem echten `ANTHROPIC_API_KEY` durchlaufen worden.**
  Verifiziert wurde bisher: `docker compose up -d --build` baut das Image
  und startet den Container sauber (Ubuntu 26.04/WSL2, ohne Docker Desktop),
  der Healthcheck wird `healthy`, die Weboberflaeche wird ausgeliefert, und
  ein echter `/ocr`-Upload gegen den Container durchlaeuft Multipart-Handling,
  Konfiguration und Fehlerpfad korrekt (erwartete 500-Antwort ohne API-Key).
  Was fehlt: derselbe Aufruf mit einem echten Key, um Tesseract-Erkennung,
  LLM-Aufruf und das fertige Text-Layer-PDF tatsaechlich zu sehen.
