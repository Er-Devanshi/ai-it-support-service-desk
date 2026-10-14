"""
Ollama Local LLM Provider implementation.
Allows offline local model execution (e.g. Llama-3, Mistral, Gemma).
"""

import httpx
from app.services.llm.base import (
    BaseLLMProvider,
    LLMResponse,
    LLMError,
    LLMTimeoutError,
)


class OllamaProvider(BaseLLMProvider):
    """Local Ollama Provider."""

    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama3", timeout_seconds: float = 60.0):
        super().__init__(model_name=model_name)
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/generate"
        body = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                res = client.post(url, json=body)
            if res.status_code == 200:
                data = res.json()
                return LLMResponse(
                    content=data.get("response", ""),
                    model=self.model_name,
                    provider="ollama",
                    raw_response=data,
                )
            raise LLMError(f"Ollama error {res.status_code}: {res.text}", provider="ollama")
        except httpx.TimeoutException:
            raise LLMTimeoutError("Ollama request timed out", provider="ollama")
        except httpx.RequestError as e:
            raise LLMError(f"Could not connect to Ollama at {self.base_url}: {e}", provider="ollama")
