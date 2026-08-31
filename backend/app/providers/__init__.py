"""Provider factory."""

from __future__ import annotations

from typing import Optional

from app.models import ProviderType, Agent
from app.providers.base import ProviderAdapter
from app.providers.claude import ClaudeAdapter
from app.providers.openai_adapter import OpenAIAdapter
from app.providers.groq_adapter import GroqAdapter
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
        return OpenAIAdapter(api_key=api_key or settings.OPENAI_API_KEY)

    if key == "groq":
        return GroqAdapter(api_key=api_key or settings.GROQ_API_KEY)

    if key == "openclaw":
        raise ProviderNotSupported("OpenClaw adapter not yet implemented")
    if key == "local":
        raise ProviderNotSupported("Local adapter not yet implemented")
    if key == "custom":
        raise ProviderNotSupported("CUSTOM provider requires a registered adapter")

    raise ProviderNotSupported(f"Unknown provider: {provider}")


def adapter_for_agent(agent: Agent) -> ProviderAdapter:
    """Build adapter from Agent row (uses api_key_env if set)."""
    import os
    api_key = None
    if agent.api_key_env:
        api_key = os.getenv(agent.api_key_env)
    return get_adapter(agent.provider, api_key=api_key)
