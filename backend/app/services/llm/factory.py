"""
LLM Provider Factory.
Instantiates the configured LLM provider according to environment settings.
Falls back safely to Mock provider in demo mode or when API key is missing.
"""

from app.config import settings
from app.services.llm.base import BaseLLMProvider, LLMConfigurationError
from app.services.llm.gemini import GeminiProvider
from app.services.llm.mock_provider import MockLLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.utils.logger import logger


def get_llm_provider(allow_fallback: bool = True) -> BaseLLMProvider:
    """
    Return an instance of the configured BaseLLMProvider.
    
    If Gemini is configured but GEMINI_API_KEY is not set:
    - If allow_fallback is True, logs a warning and returns MockLLMProvider.
    - If allow_fallback is False, raises LLMConfigurationError.
    """
    provider_name = settings.LLM_PROVIDER.lower().strip()

    if settings.DEMO_MODE or provider_name in ("mock", "demo"):
        logger.info("Using MockLLMProvider (Demo mode enabled)")
        return MockLLMProvider(model_name="mock-servicedesk-ai")

    if provider_name == "gemini":
        if not settings.GEMINI_API_KEY:
            if allow_fallback:
                logger.warning(
                    "GEMINI_API_KEY is not configured in .env. "
                    "Falling back to MockLLMProvider so the application and tests continue to function. "
                    "Set GEMINI_API_KEY to enable live Gemini AI generation."
                )
                return MockLLMProvider(model_name="mock-gemini-fallback")
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file or environment.",
                provider="gemini",
            )
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.GEMINI_MODEL or settings.LLM_MODEL,
        )

    elif provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            if allow_fallback:
                logger.warning("OPENAI_API_KEY is not set. Falling back to MockLLMProvider.")
                return MockLLMProvider(model_name="mock-openai-fallback")
            raise LLMConfigurationError("OPENAI_API_KEY is not configured.", provider="openai")
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL or settings.LLM_MODEL,
        )

    elif provider_name == "ollama":
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model_name=settings.OLLAMA_MODEL or settings.LLM_MODEL,
        )

    else:
        logger.warning(f"Unknown LLM_PROVIDER '{provider_name}'. Defaulting to MockLLMProvider.")
        return MockLLMProvider(model_name=f"mock-{provider_name}")
