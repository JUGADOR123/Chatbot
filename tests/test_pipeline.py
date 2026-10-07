from pathlib import Path

from chatbot.domain.requests import ChatRequest
from chatbot.pipeline import HelpPipeline
from chatbot.providers.mock import MockAnswerer
from chatbot.retrieval.index import DocumentIndex


def make_pipeline() -> HelpPipeline:
    index = DocumentIndex.from_cache(Path("documentation/guide-cache.json"))
    return HelpPipeline(index, MockAnswerer())


def test_pipeline_answers_supported_documented_help() -> None:
    outcome = make_pipeline().handle(ChatRequest("How do I create an auto-mcs server?"))

    assert outcome.responded is True
    assert outcome.content is not None
    assert outcome.sources
    assert outcome.sources[0].url.startswith("https://")


def test_pipeline_ignores_unrelated_messages() -> None:
    outcome = make_pipeline().handle(ChatRequest("I like pizza"))

    assert outcome.responded is False
    assert outcome.content is None
    assert outcome.reason == "not a supported help request"


def test_pipeline_ignores_supported_topic_without_help_intent() -> None:
    outcome = make_pipeline().handle(ChatRequest("auto-mcs"))

    assert outcome.responded is False