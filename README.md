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

The default mock provider runs without credentials or network access:

```powershell
chatbot
```

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

Conversation history is intentionally in memory for this first version. Real
provider adapters, streaming, and durable sessions can be added behind the
provider and storage boundaries without changing the domain models.

## Development

```powershell
python -m pytest
```