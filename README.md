# Chatbot

A small CLI chatbot foundation for experimenting with different LLM providers.

## Requirements

- Python 3.12.10
- PowerShell, bash, or another shell that can activate a virtual environment

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

For a complete local setup, the repository includes scripts that update or clone
the project, create the Python 3.12.10 environment, install local inference
support, download both Qwen GGUF models into `models/`, and write an ignored
`config.local.json`:

```bash
bash setup.sh
```

```powershell
.\setup.ps1
```

The scripts default to `https://github.com/JUGADOR123/Chatbot.git`; set `REPO_URL`
or pass `-RepoUrl` to use a fork. When run from an existing checkout, they update
that checkout instead. The scripts require
`curl` on Unix-like systems and Git plus the Python 3.12 launcher on Windows.

Optional local GGUF inference support is installed separately because it may
require a platform-specific wheel or compiler toolchain:

```powershell
python -m pip install -e ".[local]"
```

Configure it with a JSON file or environment variables. The repository keeps
`mock` and the rules classifier as defaults so tests and development do not
download models. A local setup uses a Qwen3-1.7B answer GGUF and optionally a
Qwen3-0.6B classifier GGUF:

```json
{
	"provider": "llama_cpp",
	"model": "Qwen3-1.7B",
	"model_path": "models/qwen3-1.7b-q4_k_m.gguf",
	"classifier": "qwen",
	"classifier_model_path": "models/qwen3-0.6b-q4_k_m.gguf",
	"n_ctx": 4096,
	"n_threads": 8,
	"n_gpu_layers": 0,
	"max_tokens": 384
}
```

Set `CHATBOT_CONFIG_FILE` to use a different file. `chatbot` automatically uses
`config.local.json` when it exists. The models are loaded once during startup
and the service is not ready until enabled components initialize.

The default mock provider runs without credentials or network access. At startup,
the service loads the documentation cache into an in-memory SQLite FTS5 index
before accepting messages:

```powershell
chatbot
```

Only help or problem-solving messages that match the cached documentation well
enough to pass the relevance threshold are answered. The current cache is about
Auto-MCS, so unrelated messages are ignored. Answers include the matching guide
and section internally so a future Discord adapter can render citations.

Use `chatbot --debug` to see startup readiness, classifier results, retrieval
evidence, accepted questions, and rejection reasons.

## Benchmarking

Install the benchmark dependency and run the configured model with GPU layers
disabled:

```powershell
python -m pip install -e ".[benchmark]"
python -m chatbot.benchmark --runs 3 --output benchmark-results/cpu.json
```

The report includes startup time, average/median/minimum/maximum response time,
peak process RAM, and NVIDIA VRAM observations. `nvidia-smi` values include
other GPU processes; CPU-only mode is confirmed by `n_gpu_layers=0`.

## CLI commands

Inside the chat session:

- `/help` displays available commands
- `/model` displays the active provider and model
- `/history` displays the current conversation
- `/clear` removes the current conversation
- `/quit` exits the session

Use `chatbot --help` for startup options. Configuration can be supplied through
CLI options, environment variables, or a JSON file. The current precedence is
CLI options, environment variables, config file, then defaults.

Useful environment variables include:

- `CHATBOT_CONFIG_FILE` selects a JSON configuration file.
- `CHATBOT_KNOWLEDGE_FILE` selects the documentation cache.
- `CHATBOT_MINIMUM_RELEVANCE` controls the retrieval threshold from `0` to `1`.

The documentation index is loaded once per process and released during
shutdown. Conversation history is intentionally in memory for this first
version. A real local model can be added behind the answerer interface without
changing the routing or transport boundaries.

## Development

```powershell
python -m pytest
```