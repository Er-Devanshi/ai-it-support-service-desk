"""
OpenAI API LLM Provider implementation.
Allows seamless switching to OpenAI models (e.g. gpt-4o, gpt-4o-mini).
"""

from typing import Optional, Dict, Any
import httpx
from app.services.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    LLMError,
    LLMConfigurationError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.utils.logger import logger


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider."""

    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", timeout_seconds: float = 30.0):
        super().__init__(model_name=model_name)
        if not api_key or not api_key.strip():
            raise LLMConfigurationError("OpenAI API key is missing. Set OPENAI_API_KEY in environment.", provider="openai")
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(
                    self.BASE_URL,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                return LLMResponse(
                    content=content,
                    model=self.model_name,
                    provider="openai",
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    raw_response=data,
                )
            elif res.status_code == 429:
                raise LLMRateLimitError(f"OpenAI rate limit: {res.text}", provider="openai")
            else:
                raise LLMError(f"OpenAI error {res.status_code}: {res.text}", provider="openai")
        except httpx.TimeoutException:
            raise LLMTimeoutError("OpenAI request timed out", provider="openai")
        except httpx.RequestError as e:
            raise LLMError(f"OpenAI network error: {e}", provider="openai")
