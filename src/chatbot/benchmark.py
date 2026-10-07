import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
from threading import Event, Thread
import time
from typing import Any

import psutil

from chatbot.app import ChatbotService
from chatbot.config import ConfigurationError, load_settings
from chatbot.domain.requests import ChatRequest

DEFAULT_QUERIES = (
    "How do I create a server with auto-mcs?",
    "How do I back up my server?",
    "I cannot connect to my server, what should I check?",
)


class PeakMemorySampler:
    def __init__(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.peak_rss = 0
        self._stop = Event()
        self._thread = Thread(target=self._sample, daemon=True)

    def start(self) -> None:
        self._record()
        self._thread.start()

    def stop(self) -> int:
        self._stop.set()
        self._thread.join()
        self._record()
        return self.peak_rss

    def _sample(self) -> None:
        while True:
            self._record()
            if self._stop.is_set():
                return
            time.sleep(0.02)

    def _record(self) -> None:
        self.peak_rss = max(self.peak_rss, self.process.memory_info().rss)


def _nvidia_memory() -> dict[str, Any]:
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi is None:
        return {"available": False, "reason": "nvidia-smi not found"}
    try:
        result = subprocess.run(
            [
                nvidia_smi,
                "--query-gpu=name,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        gpus = []
        for line in result.stdout.strip().splitlines():
            name, used, total = [part.strip() for part in line.split(",")]
            gpus.append({"name": name, "used_mb": int(used), "total_mb": int(total)})
        return {"available": True, "gpus": gpus}
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        return {"available": False, "reason": str(error)}


def _statistics(values: list[float]) -> dict[str, float]:
    return {
        "average_seconds": statistics.mean(values),
        "median_seconds": statistics.median(values),
        "minimum_seconds": min(values),
        "maximum_seconds": max(values),
    }


def run_benchmark(config_file: Path, queries: tuple[str, ...]) -> dict[str, Any]:
    settings = load_settings(config_file=config_file, n_gpu_layers=0, debug=False)
    if settings.provider != "llama_cpp":
        raise ConfigurationError("benchmark requires provider=llama_cpp in the config file")

    process = psutil.Process(os.getpid())
    memory_sampler = PeakMemorySampler()
    vram_before = _nvidia_memory()
    memory_sampler.start()
    startup_started = time.perf_counter()
    service = ChatbotService(settings)
    service.initialize()
    startup_seconds = time.perf_counter() - startup_started
    startup_rss = process.memory_info().rss
    vram_ready = _nvidia_memory()

    response_times: list[float] = []
    outcomes = []
    try:
        for query in queries:
            started = time.perf_counter()
            outcome = service.handle(ChatRequest(query))
            elapsed = time.perf_counter() - started
            outcomes.append({
                "query": query,
                "responded": outcome.responded,
                "reason": outcome.reason,
                "elapsed_seconds": elapsed,
            })
            if outcome.responded:
                response_times.append(elapsed)
    finally:
        service.shutdown()
    peak_rss = memory_sampler.stop()
    vram_after = _nvidia_memory()

    report: dict[str, Any] = {
        "cpu_only": settings.n_gpu_layers == 0,
        "provider": settings.provider,
        "model": settings.model,
        "classifier": settings.classifier,
        "n_gpu_layers": settings.n_gpu_layers,
        "n_threads": settings.n_threads,
        "n_ctx": settings.n_ctx,
        "max_tokens": settings.max_tokens,
        "query_count": len(queries),
        "answered_count": len(response_times),
        "startup_seconds": startup_seconds,
        "ram": {
            "startup_rss_mb": startup_rss / 1024**2,
            "peak_rss_mb": peak_rss / 1024**2,
        },
        "vram": {
            "before": vram_before,
            "ready": vram_ready,
            "after": vram_after,
            "note": "CPU-only mode requests zero GPU layers; nvidia-smi values include other processes.",
        },
        "responses": _statistics(response_times) if response_times else None,
        "outcomes": outcomes,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark the local chatbot model in CPU-only mode")
    parser.add_argument("--config", type=Path, default=Path("config.local.json"))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args(argv)
    if arguments.runs < 1:
        parser.error("--runs must be positive")
    queries = DEFAULT_QUERIES * arguments.runs
    report = run_benchmark(arguments.config, queries)
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())