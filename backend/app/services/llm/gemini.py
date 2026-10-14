"""
Gemini API LLM Provider implementation.
Direct HTTP integration with Google Generative Language API.
Includes bounded retries, quota/rate-limit error classification, and structured parsing.
"""

import time
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


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", timeout_seconds: float = 30.0):
        super().__init__(model_name=model_name)
        if not api_key or not api_key.strip():
            raise LLMConfigurationError(
                "Gemini API key is missing or empty. Please set GEMINI_API_KEY in your .env file or environment.",
                provider="gemini",
            )
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Call Gemini generateContent API with bounded retries."""
        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        max_retries = 2
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(
                        url,
                        json=body,
                        headers={"Content-Type": "application/json"},
                    )

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise LLMError("Gemini API returned an empty candidate list.", provider="gemini")
                    
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(part.get("text", "") for part in parts)
                    
                    usage_metadata = data.get("usageMetadata", {})
                    usage = {
                        "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                        "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                        "total_tokens": usage_metadata.get("totalTokenCount", 0),
                    }

                    return LLMResponse(
                        content=text,
                        model=self.model_name,
                        provider="gemini",
                        usage=usage,
                        raw_response=data,
                    )

                # Error status code classification
                error_data = {}
                try:
                    error_data = response.json().get("error", {})
                except Exception:
                    pass

                error_message = error_data.get("message", response.text)
                error_status = error_data.get("status", "")

                if response.status_code == 400 and ("API_KEY_INVALID" in error_message or "API key not valid" in error_message):
                    raise LLMConfigurationError(
                        f"Invalid Gemini API key: {error_message}. Please check your GEMINI_API_KEY.",
                        provider="gemini",
                        status_code=400,
                    )
                elif response.status_code == 429 or error_status == "RESOURCE_EXHAUSTED" or "quota" in error_message.lower():
                    raise LLMQuotaExceededError(
                        f"Gemini API quota or rate limit exceeded: {error_message}. Do not retry immediately.",
                        provider="gemini",
                        status_code=429,
                    )
                elif response.status_code in (500, 502, 503, 504):
                    # Transient server error - eligible for bounded retry
                    if attempt < max_retries:
                        logger.warning(f"Gemini API server error {response.status_code}, retrying attempt {attempt + 1}/{max_retries}...")
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    raise LLMError(
                        f"Gemini API server error {response.status_code}: {error_message}",
                        provider="gemini",
                        status_code=response.status_code,
                        retryable=True,
                    )
                else:
                    raise LLMError(
                        f"Gemini API error (HTTP {response.status_code}): {error_message}",
                        provider="gemini",
                        status_code=response.status_code,
                    )

            except httpx.TimeoutException as e:
                if attempt < max_retries:
                    logger.warning(f"Gemini API timeout, retrying attempt {attempt + 1}/{max_retries}...")
                    time.sleep(1.0)
                    continue
                raise LLMTimeoutError(
                    f"Gemini API request timed out after {self.timeout_seconds}s.",
                    provider="gemini",
                )
            except httpx.RequestError as e:
                if attempt < max_retries:
                    logger.warning(f"Gemini network error: {e}, retrying attempt {attempt + 1}/{max_retries}...")
                    time.sleep(1.0)
                    continue
                raise LLMError(
                    f"Network error connecting to Gemini API: {e}",
                    provider="gemini",
                    retryable=True,
                )

        raise LLMError("Gemini API call failed after bounded retries.", provider="gemini")
