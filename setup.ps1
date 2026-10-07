[CmdletBinding()]
param(
    [string]$RepoUrl = $env:REPO_URL,
    [string]$ProjectDir = $PSScriptRoot,
    [string]$PythonLauncher = "py"
)

$ErrorActionPreference = "Stop"
$modelDirectory = Join-Path $ProjectDir "models"

if (-not (Test-Path (Join-Path $ProjectDir ".git"))) {
    if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
        throw "Set -RepoUrl or REPO_URL to clone the project, or run this script from an existing checkout."
    }
    if ((Test-Path $ProjectDir) -and ((Get-ChildItem -Force $ProjectDir | Measure-Object).Count -gt 0)) {
        throw "Project directory is not empty and is not a Git checkout: $ProjectDir"
    }
    $parent = Split-Path -Parent $ProjectDir
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    git clone $RepoUrl $ProjectDir
}

$remoteUrl = git -C $ProjectDir config --get remote.origin.url
if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
    if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
        Write-Warning "No Git remote configured; skipping pull."
    } else {
        git -C $ProjectDir remote add origin $RepoUrl
    }
}
if (-not [string]::IsNullOrWhiteSpace((git -C $ProjectDir config --get remote.origin.url))) {
    git -C $ProjectDir pull --ff-only
}

$pythonVersion = & $PythonLauncher -3.12 -c "import platform; print(platform.python_version())"
if ($LASTEXITCODE -ne 0 -or $pythonVersion.Trim() -ne "3.12.10") {
    throw "Python 3.12.10 is required; found '$($pythonVersion.Trim())'."
}

$venvPath = Join-Path $ProjectDir ".venv"
& $PythonLauncher -3.12 -m venv $venvPath
$python = Join-Path $venvPath "Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -e ".[dev,local]"

New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null
function Get-Model([string]$Url, [string]$Destination) {
    if (Test-Path $Destination) {
        Write-Host "Already present: $Destination"
        return
    }
    Invoke-WebRequest -Uri $Url -OutFile $Destination
}

Get-Model `
    "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf?download=true" `
    (Join-Path $modelDirectory "qwen3-1.7b-q4_k_m.gguf")
Get-Model `
    "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_K_M.gguf?download=true" `
    (Join-Path $modelDirectory "qwen3-0.6b-q4_k_m.gguf")

$config = @'
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
'@
Set-Content -Path (Join-Path $ProjectDir "config.local.json") -Value $config -Encoding utf8

Write-Host ""
Write-Host "Setup complete in $ProjectDir"
Write-Host "Activate with: .\.venv\Scripts\Activate.ps1"
Write-Host "Run with: `$env:CHATBOT_CONFIG_FILE='config.local.json'; chatbot"