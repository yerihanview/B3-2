"""Backward compatibility: re-export OutputFormatter from git_agent.formatter."""

from git_agent.formatter import (
    OutputFormatter,
    MAX_COMMIT_TITLE_LEN,
    MAX_PR_TITLE_LEN,
)

__all__ = [
    "OutputFormatter",
    "MAX_COMMIT_TITLE_LEN",
    "MAX_PR_TITLE_LEN",
]
