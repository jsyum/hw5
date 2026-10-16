"""Model configuration. The ONLY model used anywhere is gpt-6-luna via OpenAI.

The OpenAI key is read from the environment (loaded from the project-root
.env file). It is never hard-coded, logged, or printed.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = "gpt-6-luna"
API_KEY_ENV = "OPENAI_API_KEY"


def _openai_api_key() -> str:
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(f"{API_KEY_ENV} is not set. Add it to the project-root .env file.")
    return key


@lru_cache(maxsize=1)
def build_model() -> OpenAIResponsesModel:
    """The single shared model object every agent uses.

    Uses OpenAI's Responses API (/v1/responses): gpt-6-luna does not accept
    function tools together with reasoning on /v1/chat/completions.
    """
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(api_key=_openai_api_key()))
