"""
Tests for Provider-Independent LLM Architecture.
Verifies mock provider, missing key handling, quota/timeout handling, and factory logic.
"""

import pytest
from unittest.mock import patch, MagicMock
import httpx
from pydantic import BaseModel

from app.services.llm.base import (
    BaseLLMProvider,
    LLMConfigurationError,
    LLMQuotaExceededError,
    LLMTimeoutError,
    LLMResponse,
)
from app.services.llm.gemini import GeminiProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.factory import get_llm_provider
from app.config import settings


class SampleSchema(BaseModel):
    category: str
    priority: str


def test_mock_llm_provider_generation():
    """Test 4: Mock LLM provider returns non-empty response clearly flagged as mock."""
    provider = MockLLMProvider()
    resp = provider.generate("How do I fix Wi-Fi?")
    assert isinstance(resp, LLMResponse)
    assert resp.is_mock is True
    assert "[Demo/Mock Mode]" in resp.content
    assert "Wi-Fi" in resp.content or "wifi" in resp.content.lower()


def test_mock_llm_structured_generation():
    """Test 4b: Mock LLM structured output parsing."""
    provider = MockLLMProvider()
    structured = provider.generate_structured(
        prompt="User reported Wi-Fi is down",
        schema=SampleSchema,
        system_instruction="Classify category and priority into JSON Schema.",
    )
    assert isinstance(structured, SampleSchema)
    assert structured.category in ("network", "general")


def test_gemini_missing_api_key_raises_error():
    """Test 5: Instantiating GeminiProvider without key raises LLMConfigurationError."""
    with pytest.raises(LLMConfigurationError) as exc_info:
        GeminiProvider(api_key="")
    assert "Gemini API key is missing" in str(exc_info.value)


def test_gemini_quota_exhausted_error_classification():
    """Test 6a: 429 RESOURCE_EXHAUSTED correctly raises LLMQuotaExceededError."""
    provider = GeminiProvider(api_key="test-dummy-key")
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.json.return_value = {
        "error": {
            "status": "RESOURCE_EXHAUSTED",
            "message": "Daily quota limit reached for free tier.",
        }
    }

    with patch("httpx.Client.post", return_value=mock_response):
        with pytest.raises(LLMQuotaExceededError) as exc_info:
            provider.generate("Test prompt")
        assert "quota or rate limit exceeded" in str(exc_info.value)


def test_gemini_timeout_error_classification():
    """Test 6b: Request timeout raises LLMTimeoutError."""
    provider = GeminiProvider(api_key="test-dummy-key", timeout_seconds=0.1)

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(LLMTimeoutError):
            provider.generate("Test prompt")


def test_llm_factory_selection():
    """Test 7: Factory correctly instantiates requested providers and falls back gracefully."""
    # When DEMO_MODE is True
    settings.DEMO_MODE = True
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)

    # When fallback is disabled and key is empty
    settings.DEMO_MODE = False
    settings.LLM_PROVIDER = "gemini"
    settings.GEMINI_API_KEY = ""
    with pytest.raises(LLMConfigurationError):
        get_llm_provider(allow_fallback=False)

    # When fallback is allowed, gracefully returns MockLLMProvider
    fallback_provider = get_llm_provider(allow_fallback=True)
    assert isinstance(fallback_provider, MockLLMProvider)
