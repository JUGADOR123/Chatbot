import re
from typing import Protocol

from chatbot.domain.requests import Audience, ClassificationResult, Intent, Topic


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
        support_terms = (
            "auto-mcs", "auto mcs", "automcs", "minecraft", "server", "world", "java",
            "mod", "plugin", "add-on", "addon", "modpack", "mrpack", "backup", "backups", "back-up",
            "restore", "whitelist", "operator", "ban", "playit", "telepath", "port", "firewall",
            "network", "networking", "friend", "friends", "download", "downloaded", "zip",
        )
        problem_terms = ("error", "issue", "problem", "cannot", "can't", "crash", "failed", "not working")
        has_support_context = any(_contains(normalized, term) for term in support_terms)
        has_help_language = any(_contains(normalized, term) for term in help_terms)
        has_problem_language = any(_contains(normalized, term) for term in problem_terms)
        intent_is_help = has_support_context and ("?" in text or has_help_language or has_problem_language)
        intent = Intent.HELP if intent_is_help else Intent.OTHER
        developer_terms = (
            "amscript", "api endpoint", "source code", "build from source", "compile",
            "python package", "contributor", "pull request", "docker image",
        )
        developer_request = any(_contains(normalized, term) for term in developer_terms)
        if developer_request:
            return ClassificationResult(Intent.OTHER, Topic.DEVELOPER, 1.0, "developer documentation is out of scope", Audience.DEVELOPER)

        topic_terms = {
            Topic.INSTALLATION: ("install", "download", "extract", "launch", "java"),
            Topic.SERVER_CREATION: ("create", "new server", "template", "import", "modpack", "mrpack"),
            Topic.SERVER_MANAGEMENT: ("start", "stop", "launch", "console", "server.properties", "world", "version"),
            Topic.ADDONS: ("mod", "plugin", "add-on", "addon", "modpack", "fabric", "forge", "paper"),
            Topic.NETWORKING: ("join", "connect", "playit", "port", "firewall", "ip", "network", "friend"),
            Topic.BACKUPS: ("backup", "back-up", "restore", "recover", "save"),
            Topic.ACCESS_CONTROL: ("operator", "op", "ban", "banned", "whitelist", "permission", "access"),
            Topic.TROUBLESHOOTING: ("error", "issue", "problem", "crash", "cannot", "can't", "failed", "not working"),
            Topic.TELEPATH: ("telepath", "remote", "pair", "pairing", "vps", "cloud"),
        }
        topic = Topic.UNKNOWN
        for candidate, terms in topic_terms.items():
            if any(_contains(normalized, term) for term in terms):
                topic = candidate
                break
        auto_mcs_terms = ("auto-mcs", "auto mcs", "automcs")
        if any(_contains(normalized, term) for term in auto_mcs_terms) and topic is Topic.UNKNOWN:
            topic = Topic.AUTO_MCS
        confidence = 1.0 if intent_is_help else 0.0
        reason = "end-user help request; retrieval will verify documentation" if intent_is_help else "not a supported help request"
        return ClassificationResult(intent, topic, confidence, reason, Audience.END_USER if intent_is_help else Audience.UNKNOWN)


def _contains(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


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