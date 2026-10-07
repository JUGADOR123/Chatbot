from pathlib import Path

import pytest

from chatbot.app import ChatbotService
from chatbot.config import ConfigurationError, Settings
from chatbot.domain.requests import ChatRequest


def test_service_is_ready_after_loading_documentation() -> None:
    service = ChatbotService(Settings(knowledge_file=Path("documentation/guide-cache.json")))

    assert service.ready is False
    service.initialize()
    try:
        assert service.ready is True
        assert service.handle(ChatRequest("How do I create an auto-mcs server?")).responded is True
    finally:
        service.shutdown()

    assert service.ready is False


def test_service_reports_missing_documentation() -> None:
    service = ChatbotService(Settings(knowledge_file=Path("missing-guide-cache.json")))

    with pytest.raises(ConfigurationError, match="could not load documentation"):
        service.initialize()