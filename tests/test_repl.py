from io import StringIO

from chatbot.providers.mock import MockProvider
from chatbot.ui.repl import Repl


def test_repl_handles_chat_and_commands() -> None:
    output = StringIO()
    inputs = iter(["hello", "/history", "/clear", "/history", "/quit"])
    repl = Repl(
        MockProvider(),
        input_stream=StringIO(),
        output_stream=output,
        prompt_reader=lambda _: next(inputs),
    )

    repl.run()

    rendered = output.getvalue()
    assert "Assistant> Mock response to: hello" in rendered
    assert "user: hello" in rendered
    assert "History cleared." in rendered
    assert rendered.endswith("Goodbye.\n")


def test_repl_handles_eof() -> None:
    output = StringIO()
    repl = Repl(
        MockProvider(),
        input_stream=StringIO(),
        output_stream=output,
    )

    repl.run()

    assert output.getvalue().endswith("Goodbye.\n")