import pytest

from chatbot.cli import main


def test_cli_help_returns_success(capsys) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    assert "Interactive CLI chatbot" in capsys.readouterr().out