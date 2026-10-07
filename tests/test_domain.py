import pytest

from chatbot.domain.models import Conversation, Message, Role


def test_conversation_tracks_and_clears_messages() -> None:
    conversation = Conversation()
    conversation.add(Message(Role.USER, "hello"))

    assert conversation.copy_messages() == (Message(Role.USER, "hello"),)
    conversation.clear()
    assert conversation.messages == []


def test_message_rejects_blank_content() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        Message(Role.USER, "  ")