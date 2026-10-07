from dataclasses import dataclass
from enum import StrEnum


class Intent(StrEnum):
    HELP = "help"
    OTHER = "other"


class Audience(StrEnum):
    END_USER = "end_user"
    DEVELOPER = "developer"
    UNKNOWN = "unknown"


class Topic(StrEnum):
    AUTO_MCS = "auto_mcs"
    INSTALLATION = "installation"
    SERVER_CREATION = "server_creation"
    SERVER_MANAGEMENT = "server_management"
    ADDONS = "addons"
    NETWORKING = "networking"
    BACKUPS = "backups"
    ACCESS_CONTROL = "access_control"
    TROUBLESHOOTING = "troubleshooting"
    TELEPATH = "telepath"
    DEVELOPER = "developer"
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
    audience: Audience = Audience.UNKNOWN

    @property
    def is_help_request(self) -> bool:
        return self.intent is Intent.HELP and self.audience is not Audience.DEVELOPER


@dataclass(frozen=True, slots=True)
class Source:
    guide: str
    section: str
    url: str
    category: str = "general"


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    responded: bool
    content: str | None = None
    sources: tuple[Source, ...] = ()
    reason: str | None = None