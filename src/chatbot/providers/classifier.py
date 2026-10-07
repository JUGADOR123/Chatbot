from typing import Protocol

from chatbot.domain.requests import ClassificationResult, Intent


class Classifier(Protocol):
    def classify(self, text: str) -> ClassificationResult:
        """Classify one incoming message without generating an answer."""


class RulesClassifier:
    def classify(self, text: str) -> ClassificationResult:
        normalized = text.lower()
        help_terms = (
            "how", "help", "why", "what", "where", "when", "error", "issue",
            "problem", "cannot", "can't", "crash",
        )
        intent_is_help = "?" in text or any(term in normalized for term in help_terms)
        topic_terms = ("auto-mcs", "auto mcs", "automcs")
        topic_is_auto_mcs = any(term in normalized for term in topic_terms)
        from chatbot.domain.requests import Intent, Topic

        intent = Intent.HELP if intent_is_help else Intent.OTHER
        topic = Topic.AUTO_MCS if topic_is_auto_mcs else Topic.UNKNOWN
        confidence = 1.0 if intent_is_help and topic_is_auto_mcs else 0.0
        reason = "supported help request" if confidence else "not a supported help request"
        return ClassificationResult(intent, topic, confidence, reason)


class FallbackClassifier:
    def __init__(self, primary: Classifier, fallback: Classifier | None = None) -> None:
        self.primary = primary
        self.fallback = fallback or RulesClassifier()

    def classify(self, text: str) -> ClassificationResult:
        primary_result = self.primary.classify(text)
        fallback_result = self.fallback.classify(text)
        if primary_result.intent is not Intent.HELP and fallback_result.intent is Intent.HELP:
            return fallback_result
        return primary_result

    def initialize(self) -> None:
        initialize = getattr(self.primary, "initialize", None)
        if initialize is not None:
            initialize()

    def close(self) -> None:
        close = getattr(self.primary, "close", None)
        if close is not None:
            close()