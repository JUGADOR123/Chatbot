import logging
import sys
from typing import TextIO

from chatbot.config import ConfigurationError, Settings
from chatbot.domain.models import Message
from chatbot.domain.requests import ChatRequest, PipelineOutcome
from chatbot.pipeline import HelpPipeline, PipelinePolicy
from chatbot.providers.base import Answerer, ChatProvider, ProviderError
from chatbot.providers.classifier import Classifier, FallbackClassifier, RulesClassifier
from chatbot.providers.llama_cpp import LlamaCppAnswerer, QwenClassifier
from chatbot.providers.mock import MockAnswerer, MockProvider
from chatbot.retrieval.index import DocumentIndex
from chatbot.ui.repl import Repl

logger = logging.getLogger(__name__)


def create_provider(settings: Settings) -> ChatProvider:
    if settings.provider == "mock":
        return MockProvider(settings.model)
    raise ConfigurationError(f"unsupported provider: {settings.provider}")


def create_answerer(settings: Settings) -> Answerer:
    if settings.provider == "mock":
        return MockAnswerer(settings.model)
    if settings.provider == "llama_cpp":
        if settings.model_path is None:
            raise ConfigurationError("model_path is required for the llama_cpp provider")
        return LlamaCppAnswerer(
            settings.model_path,
            model=settings.model,
            n_ctx=settings.n_ctx,
            n_threads=settings.n_threads,
            n_gpu_layers=settings.n_gpu_layers,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
    raise ConfigurationError(f"unsupported provider: {settings.provider}")


def create_classifier(settings: Settings) -> Classifier:
    if settings.classifier == "rules":
        return RulesClassifier()
    if settings.classifier == "qwen":
        if settings.classifier_model_path is None:
            raise ConfigurationError("classifier_model_path is required for the qwen classifier")
        return FallbackClassifier(
            QwenClassifier(
                settings.classifier_model_path,
                n_threads=settings.n_threads,
                n_gpu_layers=settings.n_gpu_layers,
            ),
            RulesClassifier(),
        )
    raise ConfigurationError(f"unsupported classifier: {settings.classifier}")


class ChatbotService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index: DocumentIndex | None = None
        self.answerer: Answerer | None = None
        self.classifier: Classifier | None = None
        self.pipeline: HelpPipeline | None = None
        self.ready = False

    def initialize(self) -> None:
        answerer: Answerer | None = None
        classifier: Classifier | None = None
        index: DocumentIndex | None = None
        try:
            logger.debug("startup: loading documentation index from %s", self.settings.knowledge_file)
            index = DocumentIndex.from_cache(self.settings.knowledge_file)
            logger.debug("startup: creating answerer provider=%s model=%s", self.settings.provider, self.settings.model)
            answerer = create_answerer(self.settings)
            logger.debug("startup: creating classifier mode=%s", self.settings.classifier)
            classifier = create_classifier(self.settings)
            logger.debug("startup: initializing answerer")
            _initialize_component(answerer)
            logger.debug("startup: initializing classifier")
            _initialize_component(classifier)
            logger.debug("startup: warming answerer")
            _warmup_component(answerer)
            self.pipeline = HelpPipeline(
                index,
                answerer,
                PipelinePolicy(self.settings.minimum_relevance),
                classifier,
            )
            self.answerer = answerer
            self.classifier = classifier
            self.index = index
            self.ready = True
            logger.debug("startup: service ready")
        except (ConfigurationError, ProviderError, ValueError) as error:
            logger.exception("startup: service initialization failed")
            _close_component(classifier)
            _close_component(answerer)
            if index is not None:
                index.close()
            raise ConfigurationError(str(error)) from error

    def handle(self, request: ChatRequest, history: tuple[Message, ...] = ()) -> PipelineOutcome:
        if not self.ready or self.pipeline is None:
            raise RuntimeError("chatbot service is not ready")
        return self.pipeline.handle(request, history)

    def shutdown(self) -> None:
        logger.debug("shutdown: releasing service resources")
        if self.index is not None:
            self.index.close()
        self.index = None
        _close_component(self.classifier)
        self.classifier = None
        _close_component(self.answerer)
        self.answerer = None
        self.ready = False
        self.pipeline = None


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


def _initialize_component(component: object) -> None:
    initialize = getattr(component, "initialize", None)
    if initialize is not None:
        initialize()


def _warmup_component(component: object) -> None:
    warmup = getattr(component, "warmup", None)
    if warmup is not None:
        warmup()


def _close_component(component: object | None) -> None:
    if component is None:
        return
    close = getattr(component, "close", None)
    if close is not None:
        close()