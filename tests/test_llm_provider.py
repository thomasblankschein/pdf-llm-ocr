import pytest

from pdf_llm_ocr import llm_ocr, llm_ocr_openai, llm_provider
from pdf_llm_ocr.config import Settings


def _settings(**overrides) -> Settings:
    base = dict(
        llm_provider="anthropic",
        anthropic_api_key="test-anthropic-key",
        anthropic_model="claude-sonnet-5",
        openai_api_key="test-openai-key",
        openai_model="gpt-5.5",
        render_dpi=300,
        tesseract_lang="deu+eng",
        max_reference_chars=8000,
        min_alignment_coverage=0.5,
    )
    base.update(overrides)
    return Settings(**base)


def test_default_provider_is_anthropic():
    provider = llm_provider.create_provider(_settings())
    assert provider.model == "claude-sonnet-5"
    assert provider.transcribe is llm_ocr.transcribe_page


def test_openai_provider_selected_by_config():
    provider = llm_provider.create_provider(_settings(llm_provider="openai"))
    assert provider.model == "gpt-5.5"
    assert provider.transcribe is llm_ocr_openai.transcribe_page


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        llm_provider.create_provider(_settings(llm_provider="mistral"))


def test_api_key_for_selects_correct_key():
    assert llm_provider.api_key_for(_settings(llm_provider="openai")) == "test-openai-key"
    assert llm_provider.api_key_for(_settings(llm_provider="anthropic")) == "test-anthropic-key"
