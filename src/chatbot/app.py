import sys
from typing import TextIO

from chatbot.config import ConfigurationError, Settings
from chatbot.providers.base import ChatProvider
from chatbot.providers.mock import MockProvider
from chatbot.ui.repl import Repl


def create_provider(settings: Settings) -> ChatProvider:
    if settings.provider == "mock":
        return MockProvider(settings.model)
    raise ConfigurationError(f"unsupported provider: {settings.provider}")


def run(
    settings: Settings,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    provider = create_provider(settings)
    Repl(
        provider,
        input_stream=input_stream or sys.stdin,
        output_stream=output_stream or sys.stdout,
    ).run()