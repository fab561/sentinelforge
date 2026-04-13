"""Abstract base class for threat intel providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ProviderResult:
    provider: str
    observable: str
    observable_type: str  # ip | domain | hash | url
    score: int            # 0–100; -1 = skipped (no key / unsupported type)
    malicious: bool = False
    tags: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    error: str | None = None

    @property
    def available(self) -> bool:
        """True when lookup ran without error and was not skipped."""
        return self.score >= 0 and self.error is None


class BaseProvider(ABC):
    """All providers must implement this interface."""

    name: str = "base"

    @abstractmethod
    async def lookup_ip(self, ip: str) -> ProviderResult: ...

    @abstractmethod
    async def lookup_domain(self, domain: str) -> ProviderResult: ...

    @abstractmethod
    async def lookup_hash(self, file_hash: str) -> ProviderResult: ...

    @abstractmethod
    async def lookup_url(self, url: str) -> ProviderResult: ...

    def _skipped(self, observable: str, observable_type: str, reason: str = "unsupported") -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            observable=observable,
            observable_type=observable_type,
            score=-1,
            error=reason,
        )

    def _error(self, observable: str, observable_type: str, exc: Exception) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            observable=observable,
            observable_type=observable_type,
            score=-1,
            error=str(exc),
        )
