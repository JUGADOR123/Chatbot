from collections.abc import Sequence
from dataclasses import dataclass

from chatbot.domain.models import Message, Role
from chatbot.domain.requests import ChatRequest, ClassificationResult, Intent, PipelineOutcome, Topic
from chatbot.providers.base import Answerer
from chatbot.providers.classifier import Classifier, RulesClassifier
from chatbot.retrieval.index import DocumentIndex


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
        classification = self.classify(request.text)
        if not classification.is_help_request:
            return PipelineOutcome(False, reason=classification.reason)
        evidence = [
            item for item in self.index.search(request.text)
            if item.score >= self.policy.minimum_relevance
        ]
        if not evidence:
            return PipelineOutcome(False, reason="no relevant documentation found")
        messages = (*history, Message(Role.USER, request.text))
        response = self.answerer.respond(messages, evidence)
        return PipelineOutcome(
            responded=True,
            content=response.content,
            sources=tuple(item.source for item in evidence),
        )