import json

import pytest

from chatbot.config import ConfigurationError, load_settings


def test_settings_precedence_is_cli_then_environment_then_file(tmp_path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"provider": "file", "model": "file-model"}), encoding="utf-8")

    settings = load_settings(
        provider="mock",
        config_file=config_file,
        environ={"CHATBOT_PROVIDER": "env", "CHATBOT_MODEL": "env-model"},
    )

    assert settings.provider == "mock"
    assert settings.model == "env-model"


def test_invalid_config_file_is_reported(tmp_path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text("not json", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="could not read"):
        load_settings(config_file=config_file, environ={})


def test_model_runtime_settings_are_loaded_and_validated() -> None:
    settings = load_settings(
        provider="llama_cpp",
        model_path="models/answer.gguf",
        classifier="qwen",
        classifier_model_path="models/classifier.gguf",
        n_ctx=2048,
        n_threads=8,
        n_gpu_layers=12,
        max_tokens=256,
        environ={},
    )

    assert settings.model_path.name == "answer.gguf"
    assert settings.classifier == "qwen"
    assert settings.classifier_model_path.name == "classifier.gguf"
    assert settings.n_gpu_layers == 12


def test_invalid_classifier_mode_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="classifier must be"):
        load_settings(classifier="unknown", environ={})