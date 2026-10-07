from collections.abc import Sequence

from chatbot.domain.models import Message, Role
from chatbot.providers.base import ProviderResponse


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