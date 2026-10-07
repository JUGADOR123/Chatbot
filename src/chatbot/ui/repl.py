from collections.abc import Callable
import logging
from typing import TextIO

from chatbot.domain.models import Conversation, Message, Role
from chatbot.domain.requests import ChatRequest
from chatbot.pipeline import HelpPipeline
from chatbot.providers.base import Answerer, ChatProvider, ProviderError

COMMANDS = ("/help", "/model", "/history", "/clear", "/quit")
logger = logging.getLogger(__name__)


class Repl:
    def __init__(
        self,
        provider: ChatProvider | Answerer,
        *,
        pipeline: HelpPipeline | None = None,
        input_stream: TextIO,
        output_stream: TextIO,
        prompt_reader: Callable[[str], str] | None = None,
    ) -> None:
        self.provider = provider
        self.pipeline = pipeline
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.conversation = Conversation()
        self._prompt_reader = prompt_reader

    def run(self) -> None:
        self._write(f"Chatbot ({self.provider.name}/{self.provider.model}). Type /help for commands.\n")
        while True:
            try:
                user_input = self._read_input("You> ")
            except (EOFError, KeyboardInterrupt):
                self._write("\nGoodbye.\n")
                return
            text = user_input.strip()
            if not text:
                continue
            if text.startswith("/"):
                if self._handle_command(text):
                    return
                continue
            self._respond(text)

    def _read_input(self, prompt: str) -> str:
        if self._prompt_reader is not None:
            return self._prompt_reader(prompt)
        self.output_stream.write(prompt)
        self.output_stream.flush()
        line = self.input_stream.readline()
        if line == "":
            raise EOFError
        return line.rstrip("\r\n")

    def _handle_command(self, text: str) -> bool:
        command, _, argument = text.partition(" ")
        if command == "/help":
            self._write("Commands: /help, /model, /history, /clear, /quit\n")
        elif command == "/model":
            self._write(f"Provider: {self.provider.name}\nModel: {self.provider.model}\n")
        elif command == "/history":
            if not self.conversation.messages:
                self._write("History is empty.\n")
            else:
                for message in self.conversation.messages:
                    self._write(f"{message.role.value}: {message.content}\n")
        elif command == "/clear":
            self.conversation.clear()
            self._write("History cleared.\n")
        elif command == "/quit":
            self._write("Goodbye.\n")
            return True
        else:
            suffix = f" {argument}" if argument else ""
            self._write(f"Unknown command: {command}{suffix}. Type /help for commands.\n")
        return False

    def _respond(self, text: str) -> None:
        if self.pipeline is not None:
            outcome = self.pipeline.handle(ChatRequest(text), self.conversation.copy_messages())
            if not outcome.responded or outcome.content is None:
                logger.debug("message ignored by pipeline: reason=%s", outcome.reason)
                return
            self.conversation.add(Message(Role.USER, text))
            self.conversation.add(Message(Role.ASSISTANT, outcome.content))
            self._write(f"Assistant> {outcome.content}\n")
            return

        self.conversation.add(Message(Role.USER, text))
        try:
            response = self.provider.respond(self.conversation.copy_messages())
        except (ProviderError, ValueError) as error:
            self._write(f"Error: {error}\n")
            return
        self.conversation.add(Message(Role.ASSISTANT, response.content))
        self._write(f"Assistant> {response.content}\n")

    def _write(self, text: str) -> None:
        self.output_stream.write(text)
        self.output_stream.flush()