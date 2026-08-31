"""Anthropic Claude adapter with client cache + tenacity retries (jittered)."""

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


def _is_retryable_anthropic(exc: BaseException) -> bool:
    """Retry on rate-limit (429) and 5xx from Anthropic SDK."""
    try:
        import anthropic
        if isinstance(exc, anthropic.RateLimitError):
            return True
        if isinstance(exc, anthropic.APIStatusError) and getattr(exc, "status_code", 0) >= 500:
            return True
        if isinstance(exc, anthropic.APIConnectionError):
            return True
        if isinstance(exc, anthropic.APITimeoutError):
            return True
    except ImportError:
        pass
    return isinstance(exc, _RETRYABLE)


class ClaudeAdapter(ProviderAdapter):
    provider_name = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Add it to .env or pass api_key=..."
            )
        self._client = None  # lazy-cached

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise ImportError(
                    "anthropic package required. pip install -r requirements-phase2.txt"
                ) from e
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def estimate_tokens(self, text: str) -> int:
        """
        Approximate token count for pre-flight budget.
        Uses OpenAI cl100k_base as a cross-model heuristic —
        Claude tokenization differs; mild overestimate is safer for budget checks.
        """
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return super().estimate_tokens(text)

    @retry(
        retry=retry_if_exception(_is_retryable_anthropic),
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
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": user}],
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str = "claude-3-5-sonnet-20241022",
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

        content_parts = []
        for block in resp.content:
            if hasattr(block, "text"):
                content_parts.append(block.text)
        content = "\n".join(content_parts)

        tokens_in = getattr(resp.usage, "input_tokens", 0) or 0
        tokens_out = getattr(resp.usage, "output_tokens", 0) or 0
        cost = estimate_cost("anthropic", model, tokens_in, tokens_out)

        return ProviderResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost_usd=cost,
            model=model,
            provider=self.provider_name,
            request_id=getattr(resp, "id", None),
            raw=resp,
        )
