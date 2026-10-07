import argparse
from pathlib import Path
import sys

from chatbot.app import run
from chatbot.config import ConfigurationError, load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive CLI chatbot")
    parser.add_argument("--provider", help="provider name (default: mock)")
    parser.add_argument("--model", help="model name (default: mock-1)")
    parser.add_argument("--config", dest="config_file", help="path to a JSON config file")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        settings = load_settings(
            provider=arguments.provider,
            model=arguments.model,
            config_file=None if arguments.config_file is None else Path(arguments.config_file),
        )
        run(settings)
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())