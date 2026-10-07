import sys
from types import SimpleNamespace

from chatbot.domain.models import Message, Role
from chatbot.providers.llama_cpp import LlamaCppAnswerer, QwenClassifier
from chatbot.retrieval.index import Evidence
from chatbot.domain.requests import Source


class FakeLlama:
    instances = []

    def __init__(self, **kwargs):
        self.settings = kwargs
        self.calls = []
        self.__class__.instances.append(self)

    def create_chat_completion(self, **kwargs):
        self.calls.append(kwargs)
        if "response_format" in kwargs:
            return {
                "choices": [{"message": {"content": '{"intent":"help","topic":"auto_mcs","confidence":0.9,"reason":"supported"}'}}]
            }
        return {"choices": [{"message": {"content": "Use the documented server setup steps."}}]}


def install_fake_llama(monkeypatch) -> None:
    FakeLlama.instances.clear()
    monkeypatch.setitem(sys.modules, "llama_cpp", SimpleNamespace(Llama=FakeLlama))


def test_answerer_loads_once_and_passes_evidence(tmp_path, monkeypatch) -> None:
    install_fake_llama(monkeypatch)
    model_path = tmp_path / "answer.gguf"
    model_path.write_bytes(b"fake")
    answerer = LlamaCppAnswerer(model_path)
    evidence = Evidence("Create a server from the template.", Source("Getting Started", "create a server", "https://example.test"), 1.0)

    answerer.initialize()
    answerer.initialize()
    response = answerer.respond((Message(Role.USER, "How do I create one?"),), (evidence,))

    assert response.content == "Use the documented server setup steps."
    assert len(FakeLlama.instances) == 1
    assert "Create a server from the template." in FakeLlama.instances[0].calls[0]["messages"][0]["content"]
    answerer.close()


def test_classifier_parses_structured_output(tmp_path, monkeypatch) -> None:
    install_fake_llama(monkeypatch)
    model_path = tmp_path / "classifier.gguf"
    model_path.write_bytes(b"fake")
    classifier = QwenClassifier(model_path)
    classifier.initialize()

    result = classifier.classify("How do I configure auto-mcs?")

    assert result.is_help_request is True
    assert result.confidence == 0.9
    classifier.close()