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
    knowledge_file: Path = Path("documentation/guide-cache.json")
    minimum_relevance: float = 0.2


def load_settings(
    *,
    provider: str | None = None,
    model: str | None = None,
    config_file: Path | None = None,
    knowledge_file: Path | None = None,
    minimum_relevance: float | None = None,
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
    values["knowledge_file"] = file_values.get("knowledge_file", "documentation/guide-cache.json")
    values["minimum_relevance"] = file_values.get("minimum_relevance", 0.2)
    if environment.get("CHATBOT_KNOWLEDGE_FILE"):
        values["knowledge_file"] = environment["CHATBOT_KNOWLEDGE_FILE"]
    if environment.get("CHATBOT_MINIMUM_RELEVANCE"):
        values["minimum_relevance"] = environment["CHATBOT_MINIMUM_RELEVANCE"]
    if knowledge_file is not None:
        values["knowledge_file"] = knowledge_file
    if minimum_relevance is not None:
        values["minimum_relevance"] = minimum_relevance

    normalized_provider = str(values["provider"]).strip().lower()
    normalized_model = str(values["model"]).strip()
    if not normalized_provider:
        raise ConfigurationError("provider cannot be empty")
    if not normalized_model:
        raise ConfigurationError("model cannot be empty")
    try:
        relevance = float(values["minimum_relevance"])
    except (TypeError, ValueError) as error:
        raise ConfigurationError("minimum relevance must be a number") from error
    if not 0 <= relevance <= 1:
        raise ConfigurationError("minimum relevance must be between 0 and 1")
    return Settings(
        provider=normalized_provider,
        model=normalized_model,
        config_file=selected_file,
        knowledge_file=Path(values["knowledge_file"]).expanduser(),
        minimum_relevance=relevance,
    )


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