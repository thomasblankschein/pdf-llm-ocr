from pdf_llm_ocr.align import align_words_to_boxes
from pdf_llm_ocr.tesseract_ocr import Word


def _word(text: str, left: int) -> Word:
    return Word(text=text, left=left, top=0, width=10, height=10)


def test_equal_words_are_kept_unchanged():
    tesseract_words = [_word("Hallo", 0), _word("Welt", 20)]
    result = align_words_to_boxes(tesseract_words, "Hallo Welt")
    assert [w.text for w in result.words] == ["Hallo", "Welt"]
    assert result.coverage == 1.0


def test_llm_correction_replaces_text_but_keeps_position():
    tesseract_words = [_word("HaIIo", 0), _word("VVelt", 20)]
    result = align_words_to_boxes(tesseract_words, "Hallo Welt")
    assert [w.text for w in result.words] == ["Hallo", "Welt"]
    assert [w.left for w in result.words] == [0, 20]
    assert result.coverage == 1.0


def test_llm_only_insertion_is_dropped_for_lack_of_position():
    tesseract_words = [_word("Hallo", 0)]
    result = align_words_to_boxes(tesseract_words, "Hallo Welt")
    assert [w.text for w in result.words] == ["Hallo"]
    assert result.coverage == 0.5


def test_tesseract_only_word_is_kept_as_fallback():
    tesseract_words = [_word("Hallo", 0), _word("Rauschen", 20)]
    result = align_words_to_boxes(tesseract_words, "Hallo")
    assert [w.text for w in result.words] == ["Hallo", "Rauschen"]
    assert result.coverage == 1.0


def test_no_tesseract_words_yields_zero_coverage():
    result = align_words_to_boxes([], "Hallo Welt wie geht es dir")
    assert result.words == []
    assert result.coverage == 0.0


def test_sparse_tesseract_words_yield_low_coverage():
    # Nur 1 von 6 LLM-Woertern hat eine Tesseract-Box - simuliert einen
    # schlechten Scan, bei dem Tesseract fast nichts findet.
    tesseract_words = [_word("geht", 0)]
    result = align_words_to_boxes(tesseract_words, "Hallo Welt wie geht es dir")
    assert result.coverage < 0.5


def test_empty_llm_text_has_full_coverage():
    result = align_words_to_boxes([], "")
    assert result.coverage == 1.0
