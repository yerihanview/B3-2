"""CLI entry point: python main.py or python src/main.py [commit|pr] [OPTIONS].

Backward-compatible entry point delegating to git_agent.cli while supporting legacy mocks.
"""

import os
import sys

# Ensure src directory is in sys.path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import git_agent.cli as cli
from git_agent.ai_client import AIClient
from git_agent.formatter import OutputFormatter
from git_agent.git_manager import GitManager

EXIT_SUCCESS = cli.EXIT_SUCCESS
EXIT_FAILURE = cli.EXIT_FAILURE
DEFAULT_MODEL = cli.DEFAULT_MODEL
DEFAULT_TEMPERATURE = cli.DEFAULT_TEMPERATURE
DEFAULT_MAX_TOKENS = cli.DEFAULT_MAX_TOKENS
COMMANDS = cli.COMMANDS
parse_args = cli.parse_args
main = cli.main


def _sync_patch() -> None:
    """Sync patched classes from current module namespace into git_agent.cli."""
    this = sys.modules.get(__name__)
    if this:
        cli.AIClient = getattr(this, "AIClient", AIClient)
        cli.GitManager = getattr(this, "GitManager", GitManager)


def _generate(*args, **kwargs):
    _sync_patch()
    return cli._generate(*args, **kwargs)


def run_cli() -> int:
    _sync_patch()
    return cli.run_cli()


__all__ = [
    "AIClient",
    "OutputFormatter",
    "GitManager",
    "EXIT_SUCCESS",
    "EXIT_FAILURE",
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
    "COMMANDS",
    "parse_args",
    "_generate",
    "run_cli",
    "main",
]

if __name__ == "__main__":
    sys.exit(run_cli())
