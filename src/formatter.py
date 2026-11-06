"""Normalize generated text into commit and pull request formats."""

import re
from typing import Final

COMMIT_PATTERN: Final = (
    r"^(?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([^()\r\n]+\))?!?: \S[^\r\n]*$"
)
PR_SECTIONS: Final = ("Why", "What", "How")


class OutputFormatter:
    """Validate commit headers and preserve PR sections."""

    @staticmethod
    def _clean(text: str) -> str:
        """Strip surrounding whitespace and an optional Markdown code fence."""
        lines = text.strip().splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines.pop()
        return "\n".join(lines).strip()

    @staticmethod
    def format_commit(raw_message: str) -> str:
        """Return a Conventional Commits message or reject an invalid header."""
        message = OutputFormatter._clean(raw_message)
        if not message or not re.fullmatch(COMMIT_PATTERN, message.splitlines()[0]):
            raise ValueError("AI output must start with a Conventional Commits header.")
        return message

    @staticmethod
    def format_pr(raw_pr: str) -> str:
        """Preserve PR content and supply explicitly unknown missing sections."""
        description = OutputFormatter._clean(raw_pr)
        for section in PR_SECTIONS:
            pattern = rf"(?im)^\s*#{{1,6}}\s+{section}\s*:?[ \t]*$"
            if not re.search(pattern, description):
                description += f"\n\n### {section}\nNot provided; review required."
        return description.strip()
