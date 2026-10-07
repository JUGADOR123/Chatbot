from dataclasses import dataclass
from typing import Protocol, Sequence

from chatbot.domain.models import Message


class ProviderError(RuntimeError):
    """Raised when a provider cannot complete a response."""


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    content: str
    model: str


class ChatProvider(Protocol):
    name: str
    model: str

    def respond(self, messages: Sequence[Message]) -> ProviderResponse:
        """Return one complete response for the supplied conversation."""