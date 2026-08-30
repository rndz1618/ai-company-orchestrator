"""Provider-agnostic adapter interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ProviderResponse:
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    model: str = ""
    provider: str = ""
    request_id: Optional[str] = None
    raw: Optional[Any] = field(default=None, repr=False)


class ProviderAdapter(ABC):
    """All provider adapters implement this interface."""

    provider_name: str = "base"

    @abstractmethod
    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> ProviderResponse:
        """Synchronous completion. Raise on hard failures."""
        ...

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate for pre-flight budget checks."""
        return max(1, len(text) // 4)
