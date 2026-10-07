import json
from collections.abc import Sequence
from pathlib import Path
from threading import Lock
from typing import Any

from chatbot.domain.models import Message, Role
from chatbot.domain.requests import Audience, ClassificationResult, Intent, Topic
from chatbot.providers.base import ProviderError, ProviderResponse
from chatbot.retrieval.index import Evidence


class LlamaCppAnswerer:
    name = "llama_cpp"

    def __init__(
        self,
        model_path: Path,
        *,
        model: str = "Qwen3-1.7B",
        n_ctx: int = 4096,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
        temperature: float = 0.2,
        max_tokens: int = 384,
    ) -> None:
        self.model = model
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llama: Any = None
        self._lock = Lock()

    def initialize(self) -> None:
        if self._llama is not None:
            return
        if not self.model_path.is_file():
            raise ProviderError(f"GGUF model file does not exist: {self.model_path}")
        try:
            from llama_cpp import Llama

            self._llama = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )
        except Exception as error:
            raise ProviderError(f"could not load GGUF model: {self.model_path}") from error

    def warmup(self) -> None:
        self._completion(
            [{"role": "user", "content": "Reply with OK."}],
            max_tokens=1,
            temperature=0,
        )

    def respond(self, messages: Sequence[Message], evidence: Sequence[Evidence]) -> ProviderResponse:
        if not evidence:
            raise ProviderError("cannot answer without documentation evidence")
        model_messages = [
            {
                "role": "system",
                "content": (
                    "/no_think\nYou are an objective technical support assistant. Answer only from the supplied "
                    "documentation evidence. If the evidence does not answer the question, say that "
                    "the documentation does not provide enough information. Do not invent commands, "
                    "settings, or facts. Do not reveal hidden reasoning. Use plain text.\n\n"
                    + _format_evidence(evidence)
                ),
            }
        ]
        model_messages.extend(
            {"role": message.role.value, "content": message.content}
            for message in messages
        )
        content = self._completion(model_messages, max_tokens=self.max_tokens, temperature=self.temperature)
        return ProviderResponse(content=content, model=self.model)

    def close(self) -> None:
        self._llama = None

    def _completion(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        if self._llama is None:
            raise ProviderError("answerer is not initialized")
        with self._lock:
            try:
                result = self._llama.create_chat_completion(
                    messages=messages,
                    top_p=0.8,
                    **kwargs,
                )
                content = result["choices"][0]["message"]["content"]
            except Exception as error:
                raise ProviderError("GGUF answer generation failed") from error
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("GGUF answer generation returned empty content")
        return _without_reasoning(content)


class QwenClassifier:
    name = "qwen_classifier"

    def __init__(
        self,
        model_path: Path,
        *,
        model: str = "Qwen3-0.6B",
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = 0,
    ) -> None:
        self.model = model
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self._llama: Any = None
        self._lock = Lock()

    def initialize(self) -> None:
        if self._llama is not None:
            return
        if not self.model_path.is_file():
            raise ProviderError(f"classifier GGUF file does not exist: {self.model_path}")
        try:
            from llama_cpp import Llama

            self._llama = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,
            )
        except Exception as error:
            raise ProviderError(f"could not load classifier GGUF model: {self.model_path}") from error

    def classify(self, text: str) -> ClassificationResult:
        prompt = (
            "Classify the user message as JSON only. Allowed intent values are help or other. "
            "Allowed topic values are auto_mcs or unknown. Use auto_mcs only when the message "
            "is about Auto-MCS. For uncertainty, use other/unknown with low confidence. "
            'Return exactly: {"intent":"help|other","topic":"auto_mcs|unknown",'
            '"confidence":0.0,"audience":"end_user|developer|unknown","reason":"short explanation"}.\n\nMessage: ' + text
        )
        try:
            result = self._completion(prompt)
            values = json.loads(result)
            intent = Intent(str(values["intent"]).lower())
            topic = Topic(str(values["topic"]).lower())
            audience = Audience(str(values.get("audience", "unknown")).lower())
            confidence = max(0.0, min(1.0, float(values["confidence"])))
            reason = str(values.get("reason", ""))[:200]
            if confidence < 0.6:
                return ClassificationResult(Intent.OTHER, Topic.UNKNOWN, confidence, "low classifier confidence", Audience.UNKNOWN)
            return ClassificationResult(intent, topic, confidence, reason, audience)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError, ProviderError):
            return ClassificationResult(Intent.OTHER, Topic.UNKNOWN, 0.0, "classifier abstained", Audience.UNKNOWN)

    def close(self) -> None:
        self._llama = None

    def _completion(self, prompt: str) -> str:
        if self._llama is None:
            raise ProviderError("classifier is not initialized")
        with self._lock:
            try:
                result = self._llama.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    max_tokens=96,
                    response_format={"type": "json_object"},
                )
                content = result["choices"][0]["message"]["content"]
            except Exception as error:
                raise ProviderError("GGUF classification failed") from error
        if not isinstance(content, str):
            raise ProviderError("classifier returned invalid content")
        return content


def _format_evidence(evidence: Sequence[Evidence]) -> str:
    return "\n\n".join(
        f"[{item.source.guide} / {item.source.section}]\n{item.text}"
        for item in evidence
    )


def _without_reasoning(content: str) -> str:
    if "</think>" in content:
        content = content.rsplit("</think>", 1)[-1]
    return content.replace("<think>", "").strip()