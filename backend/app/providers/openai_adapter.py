"""OpenAI adapter with client cache + tenacity retries (jittered)."""

from __future__ import annotations

import logging
import os
from typing import Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
    before_sleep_log,
)

from app.providers.base import ProviderAdapter, ProviderResponse
from app.services.budget import estimate_cost

logger = logging.getLogger(__name__)

_RETRYABLE = (ConnectionError, TimeoutError, OSError)


def _is_retryable_openai(exc: BaseException) -> bool:
    try:
        import openai
        if isinstance(exc, openai.RateLimitError):
            return True
        if isinstance(exc, openai.APIStatusError) and getattr(exc, "status_code", 0) >= 500:
            return True
        if isinstance(exc, openai.APIConnectionError):
            return True
        if isinstance(exc, openai.APITimeoutError):
            return True
    except ImportError:
        pass
    return isinstance(exc, _RETRYABLE)


class OpenAIAdapter(ProviderAdapter):
    provider_name = "openai"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Add it to .env or pass api_key=..."
            )
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import openai
            except ImportError as e:
                raise ImportError(
                    "openai package required. pip install -r requirements-phase2.txt"
                ) from e
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    def estimate_tokens(self, text: str) -> int:
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return super().estimate_tokens(text)

    @retry(
        retry=retry_if_exception(_is_retryable_openai),
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=1),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _call_api(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ):
        client = self._get_client()
        return client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": user},
            ],
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        resp = self._call_api(
            system=system,
            user=user,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        choice = resp.choices[0] if resp.choices else None
        content = choice.message.content if choice and choice.message else ""

        usage = getattr(resp, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", 0) or 0
        tokens_out = getattr(usage, "completion_tokens", 0) or 0
        cost = estimate_cost("openai", model, tokens_in, tokens_out)

        return ProviderResponse(
            content=content or "",
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost_usd=cost,
            model=model,
            provider=self.provider_name,
            request_id=getattr(resp, "id", None),
            raw=resp,
        )
