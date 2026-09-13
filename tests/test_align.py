from pdf_llm_ocr.align import align_words_to_boxes
from pdf_llm_ocr.tesseract_ocr import Word


def _word(text: str, left: int) -> Word:
    return Word(text=text, left=left, top=0, width=10, height=10)


def test_equal_words_are_kept_unchanged():
    tesseract_words = [_word("Hallo", 0), _word("Welt", 20)]
    aligned = align_words_to_boxes(tesseract_words, "Hallo Welt")
    assert [w.text for w in aligned] == ["Hallo", "Welt"]


def test_llm_correction_replaces_text_but_keeps_position():
    tesseract_words = [_word("HaIIo", 0), _word("VVelt", 20)]
    aligned = align_words_to_boxes(tesseract_words, "Hallo Welt")
    assert [w.text for w in aligned] == ["Hallo", "Welt"]
    assert [w.left for w in aligned] == [0, 20]


def test_llm_only_insertion_is_dropped_for_lack_of_position():
    tesseract_words = [_word("Hallo", 0)]
    aligned = align_words_to_boxes(tesseract_words, "Hallo Welt")
    assert [w.text for w in aligned] == ["Hallo"]


def test_tesseract_only_word_is_kept_as_fallback():
    tesseract_words = [_word("Hallo", 0), _word("Rauschen", 20)]
    aligned = align_words_to_boxes(tesseract_words, "Hallo")
    assert [w.text for w in aligned] == ["Hallo", "Rauschen"]
