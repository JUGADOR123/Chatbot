import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when chatbot configuration cannot be loaded or validated."""


@dataclass(frozen=True, slots=True)
class Settings:
    provider: str = "mock"
    model: str = "mock-1"
    config_file: Path | None = None


def load_settings(
    *,
    provider: str | None = None,
    model: str | None = None,
    config_file: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Settings:
    environment = os.environ if environ is None else environ
    selected_file = config_file or _config_path(environment)
    file_values = _read_config(selected_file)

    values: dict[str, Any] = {
        "provider": file_values.get("provider", "mock"),
        "model": file_values.get("model", "mock-1"),
    }
    if environment.get("CHATBOT_PROVIDER"):
        values["provider"] = environment["CHATBOT_PROVIDER"]
    if environment.get("CHATBOT_MODEL"):
        values["model"] = environment["CHATBOT_MODEL"]
    if provider is not None:
        values["provider"] = provider
    if model is not None:
        values["model"] = model

    normalized_provider = str(values["provider"]).strip().lower()
    normalized_model = str(values["model"]).strip()
    if not normalized_provider:
        raise ConfigurationError("provider cannot be empty")
    if not normalized_model:
        raise ConfigurationError("model cannot be empty")
    return Settings(normalized_provider, normalized_model, selected_file)


def _config_path(environ: dict[str, str]) -> Path | None:
    configured_path = environ.get("CHATBOT_CONFIG_FILE")
    return Path(configured_path).expanduser() if configured_path else None


def _read_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as config_handle:
            values = json.load(config_handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"could not read config file: {path}") from error
    if not isinstance(values, dict):
        raise ConfigurationError("config file must contain a JSON object")
    return values