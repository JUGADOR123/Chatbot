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