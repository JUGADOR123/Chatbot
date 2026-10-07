#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$SCRIPT_DIR}"
REPO_URL="${REPO_URL:-https://github.com/JUGADOR123/Chatbot.git}"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
MODEL_DIR="$PROJECT_DIR/models"

if [[ ! -d "$PROJECT_DIR/.git" ]]; then
    # The repository URL defaults to the project's public origin.
    if [[ -e "$PROJECT_DIR" && -n "$(find "$PROJECT_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
        echo "Project directory is not empty and is not a Git checkout: $PROJECT_DIR" >&2
        exit 1
    fi
    mkdir -p "$(dirname "$PROJECT_DIR")"
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

if ! git -C "$PROJECT_DIR" config remote.origin.url >/dev/null 2>&1; then
    if [[ -n "$REPO_URL" ]]; then
        git -C "$PROJECT_DIR" remote add origin "$REPO_URL"
    else
        echo "No Git remote configured; skipping pull."
    fi
fi
if git -C "$PROJECT_DIR" config remote.origin.url >/dev/null 2>&1; then
    git -C "$PROJECT_DIR" pull --ff-only
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.12.10 was not found as '$PYTHON_BIN'. Set PYTHON_BIN to its executable." >&2
    exit 1
fi

PYTHON_VERSION="$($PYTHON_BIN -c 'import platform; print(platform.python_version())')"
if [[ "$PYTHON_VERSION" != "3.12.10" ]]; then
    echo "Python 3.12.10 is required; found $PYTHON_VERSION." >&2
    exit 1
fi

cd "$PROJECT_DIR"
"$PYTHON_BIN" -m venv .venv
PYTHON=".venv/bin/python"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -e '.[dev,local]'

mkdir -p "$MODEL_DIR"
download_model() {
    local url="$1"
    local destination="$2"
    local expected_size="$3"
    if [[ -f "$destination" && "$(wc -c < "$destination")" -eq "$expected_size" ]]; then
        echo "Already present: $destination"
        return
    fi
    rm -f "$destination" "${destination}.part"
    curl --fail --location --retry 3 --progress-bar "$url" --output "${destination}.part"
    if [[ "$(wc -c < "${destination}.part")" -ne "$expected_size" ]]; then
        rm -f "${destination}.part"
        echo "Downloaded file has an unexpected size: $destination" >&2
        exit 1
    fi
    mv "${destination}.part" "$destination"
}

download_model \
    "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf?download=true" \
    "$MODEL_DIR/qwen3-1.7b-q4_k_m.gguf" \
    1282439584
download_model \
    "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true" \
    "$MODEL_DIR/qwen3-0.6b-q4_k_m.gguf" \
    484220320

cat > config.local.json <<'JSON'
{
  "provider": "llama_cpp",
  "model": "Qwen3-1.7B",
  "model_path": "models/qwen3-1.7b-q4_k_m.gguf",
  "classifier": "qwen",
  "classifier_model_path": "models/qwen3-0.6b-q4_k_m.gguf",
  "n_ctx": 4096,
  "n_threads": 4,
  "n_gpu_layers": 0,
  "temperature": 0.2,
  "max_tokens": 384
}
JSON

echo
echo "Setup complete in $PROJECT_DIR"
echo "Activate with: source .venv/bin/activate"
echo "Run with: chatbot --debug"