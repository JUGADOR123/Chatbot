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
    model_path: Path | None = None
    classifier: str = "rules"
    classifier_model_path: Path | None = None
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0
    temperature: float = 0.2
    max_tokens: int = 384
    debug: bool = False


def load_settings(
    *,
    provider: str | None = None,
    model: str | None = None,
    config_file: Path | None = None,
    knowledge_file: Path | None = None,
    minimum_relevance: float | None = None,
    model_path: Path | None = None,
    classifier: str | None = None,
    classifier_model_path: Path | None = None,
    n_ctx: int | None = None,
    n_threads: int | None = None,
    n_gpu_layers: int | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    debug: bool | None = None,
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
    values.update({
        "model_path": file_values.get("model_path"),
        "classifier": file_values.get("classifier", "rules"),
        "classifier_model_path": file_values.get("classifier_model_path"),
        "n_ctx": file_values.get("n_ctx", 4096),
        "n_threads": file_values.get("n_threads", 4),
        "n_gpu_layers": file_values.get("n_gpu_layers", 0),
        "temperature": file_values.get("temperature", 0.2),
        "max_tokens": file_values.get("max_tokens", 384),
        "debug": file_values.get("debug", False),
    })
    for key, environment_key in {
        "model_path": "CHATBOT_MODEL_PATH",
        "classifier": "CHATBOT_CLASSIFIER",
        "classifier_model_path": "CHATBOT_CLASSIFIER_MODEL_PATH",
        "n_ctx": "CHATBOT_N_CTX",
        "n_threads": "CHATBOT_N_THREADS",
        "n_gpu_layers": "CHATBOT_N_GPU_LAYERS",
        "temperature": "CHATBOT_TEMPERATURE",
        "max_tokens": "CHATBOT_MAX_TOKENS",
        "debug": "CHATBOT_DEBUG",
    }.items():
        if environment.get(environment_key):
            values[key] = environment[environment_key]
    for key, value in {
        "model_path": model_path,
        "classifier": classifier,
        "classifier_model_path": classifier_model_path,
        "n_ctx": n_ctx,
        "n_threads": n_threads,
        "n_gpu_layers": n_gpu_layers,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "debug": debug,
    }.items():
        if value is not None:
            values[key] = value

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
    normalized_classifier = str(values["classifier"]).strip().lower()
    if normalized_classifier not in {"rules", "qwen"}:
        raise ConfigurationError("classifier must be 'rules' or 'qwen'")
    try:
        numeric_values = {
            "n_ctx": int(values["n_ctx"]),
            "n_threads": int(values["n_threads"]),
            "n_gpu_layers": int(values["n_gpu_layers"]),
            "temperature": float(values["temperature"]),
            "max_tokens": int(values["max_tokens"]),
        }
    except (TypeError, ValueError) as error:
        raise ConfigurationError("model runtime settings must be numeric") from error
    if numeric_values["n_ctx"] < 512 or numeric_values["n_threads"] < 1 or numeric_values["max_tokens"] < 1:
        raise ConfigurationError("context, threads, and max tokens must be positive and sufficiently large")
    if numeric_values["n_gpu_layers"] < 0 or numeric_values["temperature"] < 0:
        raise ConfigurationError("GPU layers and temperature cannot be negative")
    debug_value = _parse_bool(values["debug"])
    return Settings(
        provider=normalized_provider,
        model=normalized_model,
        config_file=selected_file,
        knowledge_file=Path(values["knowledge_file"]).expanduser(),
        minimum_relevance=relevance,
        model_path=_optional_path(values["model_path"]),
        classifier=normalized_classifier,
        classifier_model_path=_optional_path(values["classifier_model_path"]),
        **numeric_values,
        debug=debug_value,
    )


def _config_path(environ: dict[str, str]) -> Path | None:
    configured_path = environ.get("CHATBOT_CONFIG_FILE")
    return Path(configured_path).expanduser() if configured_path else None


def _optional_path(value: Any) -> Path | None:
    return Path(value).expanduser() if value else None


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off", ""}:
        return False
    raise ConfigurationError("debug must be a boolean")


def _read_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8-sig") as config_handle:
            values = json.load(config_handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"could not read config file: {path}") from error
    if not isinstance(values, dict):
        raise ConfigurationError("config file must contain a JSON object")
    return values