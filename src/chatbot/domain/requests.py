from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    HELP = "help"
    OTHER = "other"


class Topic(StrEnum):
    AUTO_MCS = "auto_mcs"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ChatRequest:
    text: str


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    intent: Intent
    topic: Topic
    confidence: float
    reason: str

    @property
    def is_help_request(self) -> bool:
        return self.intent is Intent.HELP and self.topic is Topic.AUTO_MCS


@dataclass(frozen=True, slots=True)
class Source:
    guide: str
    section: str
    url: str


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    responded: bool
    content: str | None = None
    sources: tuple[Source, ...] = ()
    reason: str | None = None