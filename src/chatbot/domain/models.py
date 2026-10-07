from dataclasses import dataclass, field
from enum import StrEnum


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("message content cannot be empty")


@dataclass(slots=True)
class Conversation:
    messages: list[Message] = field(default_factory=list)

    def add(self, message: Message) -> None:
        self.messages.append(message)

    def clear(self) -> None:
        self.messages.clear()

    def copy_messages(self) -> tuple[Message, ...]:
        return tuple(self.messages)