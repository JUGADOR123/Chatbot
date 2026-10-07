from collections.abc import Sequence
from dataclasses import dataclass
import logging

from chatbot.domain.models import Message, Role
from chatbot.domain.requests import ChatRequest, ClassificationResult, Intent, PipelineOutcome, Topic
from chatbot.providers.base import Answerer
from chatbot.providers.classifier import Classifier, RulesClassifier
from chatbot.retrieval.index import DocumentIndex

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PipelinePolicy:
    minimum_relevance: float = 0.2


class HelpPipeline:
    def __init__(
        self,
        index: DocumentIndex,
        answerer: Answerer,
        policy: PipelinePolicy | None = None,
        classifier: Classifier | None = None,
    ) -> None:
        self.index = index
        self.answerer = answerer
        self.policy = policy or PipelinePolicy()
        self.classifier = classifier or RulesClassifier()

    def classify(self, text: str) -> ClassificationResult:
        return self.classifier.classify(text)

    def handle(self, request: ChatRequest, history: Sequence[Message] = ()) -> PipelineOutcome:
        logger.debug("message received: %r", request.text[:200])
        classification = self.classify(request.text)
        logger.debug(
            "classification: intent=%s topic=%s confidence=%.2f reason=%s",
            classification.intent,
            classification.topic,
            classification.confidence,
            classification.reason,
        )
        if not classification.is_help_request:
            logger.debug("message rejected: stage=classifier reason=%s", classification.reason)
            return PipelineOutcome(False, reason=classification.reason)
        evidence = [
            item for item in self.index.search(request.text)
            if item.score >= self.policy.minimum_relevance
        ]
        if not evidence:
            logger.debug("message rejected: stage=retrieval reason=no relevant documentation")
            return PipelineOutcome(False, reason="no relevant documentation found")
        messages = (*history, Message(Role.USER, request.text))
        logger.debug(
            "message accepted: evidence=%s",
            ", ".join(f"{item.source.guide}/{item.source.section} ({item.score:.2f})" for item in evidence),
        )
        response = self.answerer.respond(messages, evidence)
        return PipelineOutcome(
            responded=True,
            content=response.content,
            sources=tuple(item.source for item in evidence),
        )