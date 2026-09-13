"""Verheiratet Tesseract-Positionen mit LLM-Textqualitaet.

Tesseract liefert Woerter *mit* Bounding-Box, aber schlechterer Texttreue.
Das LLM liefert einen zusammenhaengenden, korrigierten Fliesstext *ohne*
Positionen. Wir richten beide Wortfolgen per Sequence-Alignment (difflib)
aneinander aus und uebernehmen je aligniertem Paar den LLM-Text auf der
Tesseract-Box.

Bekannte Grenzen dieses Heuristik-Ansatzes (bewusst nicht geloest im
Grundgeruest, siehe README "Naechste Schritte"):
- Woerter, die das LLM zusaetzlich erkennt (insert-Bloecke) haben keine Box
  und werden verworfen statt platziert.
- Bei ungleich langen replace-Bloecken (z.B. LLM trennt/verbindet Woerter
  anders als Tesseract) werden ueberzaehlige Tesseract-Woerter unveraendert
  uebernommen statt neu aufgeteilt.
"""

import difflib

from .tesseract_ocr import Word


def align_words_to_boxes(tesseract_words: list[Word], llm_text: str) -> list[Word]:
    llm_tokens = llm_text.split()
    tesseract_tokens = [word.text for word in tesseract_words]

    matcher = difflib.SequenceMatcher(a=tesseract_tokens, b=llm_tokens, autojunk=False)
    aligned: list[Word] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            aligned.extend(tesseract_words[i1:i2])
            continue

        if tag == "delete":
            # Tesseract sah hier Woerter, die im LLM-Text keine Entsprechung
            # haben (z.B. Rauschen). Original beibehalten, statt Text zu verlieren.
            aligned.extend(tesseract_words[i1:i2])
            continue

        if tag == "insert":
            # LLM-Woerter ohne Tesseract-Box: keine Position verfuegbar, verwerfen.
            continue

        if tag == "replace":
            tesseract_slice = tesseract_words[i1:i2]
            llm_slice = llm_tokens[j1:j2]
            for offset, tesseract_word in enumerate(tesseract_slice):
                if offset < len(llm_slice):
                    aligned.append(
                        Word(
                            text=llm_slice[offset],
                            left=tesseract_word.left,
                            top=tesseract_word.top,
                            width=tesseract_word.width,
                            height=tesseract_word.height,
                        )
                    )
                else:
                    aligned.append(tesseract_word)

    return aligned
