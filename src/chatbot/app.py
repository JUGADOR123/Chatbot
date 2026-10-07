import sys
from typing import TextIO

from chatbot.config import ConfigurationError, Settings
from chatbot.domain.models import Message
from chatbot.domain.requests import ChatRequest, PipelineOutcome
from chatbot.pipeline import HelpPipeline, PipelinePolicy
from chatbot.providers.base import Answerer, ChatProvider
from chatbot.providers.mock import MockAnswerer, MockProvider
from chatbot.retrieval.index import DocumentIndex
from chatbot.ui.repl import Repl


def create_provider(settings: Settings) -> ChatProvider:
    if settings.provider == "mock":
        return MockProvider(settings.model)
    raise ConfigurationError(f"unsupported provider: {settings.provider}")


def create_answerer(settings: Settings) -> Answerer:
    if settings.provider == "mock":
        return MockAnswerer(settings.model)
    raise ConfigurationError(f"unsupported provider: {settings.provider}")


class ChatbotService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index: DocumentIndex | None = None
        self.answerer: Answerer | None = None
        self.pipeline: HelpPipeline | None = None
        self.ready = False

    def initialize(self) -> None:
        try:
            index = DocumentIndex.from_cache(self.settings.knowledge_file)
        except ValueError as error:
            raise ConfigurationError(str(error)) from error
        answerer = create_answerer(self.settings)
        self.pipeline = HelpPipeline(
            index,
            answerer,
            PipelinePolicy(self.settings.minimum_relevance),
        )
        self.answerer = answerer
        self.index = index
        self.ready = True

    def handle(self, request: ChatRequest, history: tuple[Message, ...] = ()) -> PipelineOutcome:
        if not self.ready or self.pipeline is None:
            raise RuntimeError("chatbot service is not ready")
        return self.pipeline.handle(request, history)

    def shutdown(self) -> None:
        if self.index is not None:
            self.index.close()
        self.index = None
        self.ready = False
        self.pipeline = None
        self.answerer = None


def run(
    settings: Settings,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    service = ChatbotService(settings)
    service.initialize()
    try:
        if service.answerer is None or service.pipeline is None:
            raise RuntimeError("chatbot service did not become ready")
        Repl(
            service.answerer,
            pipeline=service.pipeline,
            input_stream=input_stream or sys.stdin,
            output_stream=output_stream or sys.stdout,
        ).run()
    finally:
        service.shutdown()