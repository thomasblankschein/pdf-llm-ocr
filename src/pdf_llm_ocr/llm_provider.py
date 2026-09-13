"""Waehlt anhand der Config den LLM-Provider (Anthropic/Claude oder OpenAI) aus.

Beide Provider-Module (llm_ocr.py, llm_ocr_openai.py) haben dieselbe
transcribe_page(client, model, image, reference_text, max_reference_chars)
Signatur - pipeline.py muss den gewaehlten Provider daher nicht kennen.
"""

from dataclasses import dataclass
from typing import Callable, Protocol

import anthropic
import openai
from PIL import Image

from . import llm_ocr, llm_ocr_openai
from .config import Settings

SUPPORTED_PROVIDERS = ("anthropic", "openai")


class Transcriber(Protocol):
    def __call__(
        self,
        client: object,
        model: str,
        image: Image.Image,
        reference_text: str,
        max_reference_chars: int,
    ) -> str: ...


@dataclass
class LlmProvider:
    client: object
    model: str
    transcribe: Callable[..., str]


def create_provider(settings: Settings) -> LlmProvider:
    if settings.llm_provider == "openai":
        return LlmProvider(
            client=openai.OpenAI(api_key=settings.openai_api_key),
            model=settings.openai_model,
            transcribe=llm_ocr_openai.transcribe_page,
        )
    if settings.llm_provider == "anthropic":
        return LlmProvider(
            client=anthropic.Anthropic(api_key=settings.anthropic_api_key),
            model=settings.anthropic_model,
            transcribe=llm_ocr.transcribe_page,
        )
    raise ValueError(
        f"Unbekannter PDF_LLM_OCR_PROVIDER '{settings.llm_provider}' - erwartet einen von {SUPPORTED_PROVIDERS}"
    )


def api_key_for(settings: Settings) -> str:
    if settings.llm_provider == "openai":
        return settings.openai_api_key
    return settings.anthropic_api_key
