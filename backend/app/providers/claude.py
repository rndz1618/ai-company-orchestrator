"""Anthropic Claude adapter with client cache + retries on rate-limit/5xx."""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

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
        if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:
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
        Uses OpenAI cl100k_base as a cross-model heuristic — Claude
        tokenization differs; mild overestimate is safer for budget checks.
        """
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return super().estimate_tokens(text)

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        last_exc: Optional[Exception] = None
        resp = None
        for attempt in range(1, 5):
            try:
                client = self._get_client()
                resp = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system or "You are a helpful assistant.",
                    messages=[{"role": "user", "content": user}],
                )
                break
            except Exception as e:
                last_exc = e
                if not _is_retryable_anthropic(e) or attempt == 4:
                    raise
                wait_s = min(30, 2 ** (attempt - 1))
                logger.warning(
                    "Claude API retryable error (attempt %s/4, wait %ss): %s",
                    attempt, wait_s, e,
                )
                time.sleep(wait_s)
        else:
            raise last_exc  # type: ignore

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
