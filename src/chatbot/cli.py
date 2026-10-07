import argparse
import logging
import os
from pathlib import Path
import sys

from chatbot.app import run
from chatbot.config import ConfigurationError, load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive CLI chatbot")
    parser.add_argument("--provider", help="provider name (default: mock)")
    parser.add_argument("--model", help="model name (default: mock-1)")
    parser.add_argument("--config", dest="config_file", help="path to a JSON config file")
    parser.add_argument("--debug", action="store_true", help="log startup and routing decisions")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        config_file = None
        if arguments.config_file is not None:
            config_file = Path(arguments.config_file)
        elif not os.environ.get("CHATBOT_CONFIG_FILE"):
            local_config = Path("config.local.json")
            if local_config.is_file():
                config_file = local_config
        settings = load_settings(
            provider=arguments.provider,
            model=arguments.model,
            config_file=config_file,
            debug=True if arguments.debug else None,
        )
        logging.basicConfig(
            level=logging.DEBUG if settings.debug else logging.WARNING,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        logging.getLogger(__name__).debug("loaded settings: %s", settings)
        run(settings)
    except ConfigurationError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())