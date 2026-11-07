"""git_agent: Automated Git commit message and PR description generator."""

from .ai_client import (
    AIClient,
    AIClientError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServerError,
)
from .formatter import MAX_COMMIT_TITLE_LEN, MAX_PR_TITLE_LEN, OutputFormatter
from .git_manager import GitManager
from .cli import run_cli, parse_args, main

__version__ = "1.0.0"
__all__ = [
    "AIClient",
    "AIClientError",
    "AuthenticationError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "OutputFormatter",
    "MAX_COMMIT_TITLE_LEN",
    "MAX_PR_TITLE_LEN",
    "GitManager",
    "run_cli",
    "parse_args",
    "main",
]
