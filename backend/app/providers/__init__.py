"""Provider factory."""

from __future__ import annotations

from typing import Optional

from app.models import ProviderType, Agent
from app.providers.base import ProviderAdapter
from app.providers.claude import ClaudeAdapter
from app.core.config import settings


class ProviderNotSupported(Exception):
    pass


def get_adapter(provider: ProviderType | str, api_key: Optional[str] = None) -> ProviderAdapter:
    """Return the right adapter for a provider type."""
    if isinstance(provider, ProviderType):
        key = provider.value
    else:
        key = str(provider).lower()

    if key in ("anthropic", "claude"):
        return ClaudeAdapter(api_key=api_key or settings.ANTHROPIC_API_KEY)

    if key == "openai":
        raise ProviderNotSupported("OpenAI adapter lands in a later Phase 2 increment")
    if key == "openclaw":
        raise ProviderNotSupported("OpenClaw adapter not yet implemented")
    if key == "local":
        raise ProviderNotSupported("Local adapter not yet implemented")

    raise ProviderNotSupported(f"Unknown provider: {provider}")


def adapter_for_agent(agent: Agent) -> ProviderAdapter:
    """Build adapter from Agent row (uses api_key_env if set)."""
    import os
    api_key = None
    if agent.api_key_env:
        api_key = os.getenv(agent.api_key_env)
    return get_adapter(agent.provider, api_key=api_key)
