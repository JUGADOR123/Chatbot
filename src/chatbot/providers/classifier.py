from typing import Protocol

from chatbot.domain.requests import ClassificationResult


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