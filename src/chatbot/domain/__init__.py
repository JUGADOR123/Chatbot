"""Core conversation types independent of providers and terminal rendering."""

from chatbot.domain.models import Conversation, Message, Role

__all__ = ["Conversation", "Message", "Role"]