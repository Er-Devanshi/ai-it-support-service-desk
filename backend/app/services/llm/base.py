"""
Base LLM Provider abstraction and shared data models.
Enforces provider independence across Gemini, OpenAI, Ollama, and Mock providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type, TypeVar
import json
import re
from pydantic import BaseModel, Field
from app.utils.logger import logger

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM provider errors."""
    def __init__(self, message: str, provider: str = "", status_code: Optional[int] = None, retryable: bool = False):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.retryable = retryable


class LLMConfigurationError(LLMError):
    """Raised when required LLM configuration or API key is missing."""
    pass


class LLMQuotaExceededError(LLMError):
    """Raised when provider quota or daily limit is exhausted."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when provider rate limit is exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when provider times out."""
    pass


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    content: str
    model: str
    provider: str
    is_mock: bool = False
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


class BaseLLMProvider(ABC):
    """Abstract interface that all LLM providers must implement."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Generate a natural language text response."""
        pass

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: str = "",
        max_tokens: int = 1024,
    ) -> T:
        """
        Generate structured output adhering to a Pydantic schema.
        Default implementation instructs the model to return valid JSON and parses it.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        structured_system = (
            f"{system_instruction}\n\n"
            f"CRITICAL: You must respond ONLY with a single valid JSON object adhering strictly "
            f"to the following JSON Schema. Do NOT include markdown code fences, comments, or extra text.\n"
            f"JSON Schema:\n{schema_json}"
        )
        response = self.generate(
            prompt=prompt,
            system_instruction=structured_system,
            max_tokens=max_tokens,
            temperature=0.0,
        )

        content = response.content.strip()
        # Clean markdown code fences if model enclosed JSON in ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if fence_match:
            clean_json = fence_match.group(1).strip()
        else:
            clean_json = content

        try:
            parsed = json.loads(clean_json)
            return schema.model_validate(parsed)
        except Exception as e:
            logger.warning(f"Failed to parse structured response from {self.__class__.__name__}: {e}. Raw content: {content[:200]}")
            # Try finding outermost JSON object
            obj_match = re.search(r"\{[\s\S]*\}", clean_json)
            if obj_match:
                parsed = json.loads(obj_match.group(0))
                return schema.model_validate(parsed)
            raise LLMError(f"Malformed structured response from {self.__class__.__name__}: {e}", provider=self.__class__.__name__)
