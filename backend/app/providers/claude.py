"""Anthropic Claude adapter."""

from __future__ import annotations

import os
from typing import Optional

from app.providers.base import ProviderAdapter, ProviderResponse
from app.services.budget import estimate_cost


class ClaudeAdapter(ProviderAdapter):
    provider_name = "anthropic"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Add it to .env or pass api_key=..."
            )

    def _client(self):
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required. pip install -r requirements-phase2.txt"
            ) from e
        return anthropic.Anthropic(api_key=self.api_key)

    def estimate_tokens(self, text: str) -> int:
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
        client = self._client()
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": user}],
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
