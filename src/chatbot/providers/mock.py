from collections.abc import Sequence

from chatbot.domain.models import Message, Role
from chatbot.providers.base import ProviderResponse
from chatbot.retrieval.index import Evidence


class MockProvider:
    name = "mock"

    def __init__(self, model: str = "mock-1") -> None:
        self.model = model

    def respond(self, messages: Sequence[Message]) -> ProviderResponse:
        user_messages = [message.content for message in messages if message.role is Role.USER]
        if not user_messages:
            raise ValueError("the conversation must contain a user message")
        prompt = user_messages[-1]
        return ProviderResponse(
            content=f"Mock response to: {prompt}",
            model=self.model,
        )


class MockAnswerer:
    name = "mock"

    def __init__(self, model: str = "mock-answerer") -> None:
        self.model = model

    def initialize(self) -> None:
        return

    def warmup(self) -> None:
        return

    def close(self) -> None:
        return

    def respond(self, messages: Sequence[Message], evidence: Sequence[Evidence]) -> ProviderResponse:
        if not messages or not evidence:
            raise ValueError("an answer requires a message and documentation evidence")
        source = evidence[0].source
        return ProviderResponse(
            content=f"According to {source.guide} / {source.section}: {evidence[0].text.splitlines()[0]}",
            model=self.model,
        )