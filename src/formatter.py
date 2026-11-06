"""Normalize generated text into commit and pull request formats with strict length and section validation."""

import re
from typing import Final

COMMIT_PATTERN: Final = (
    r"^(?:feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([^()\r\n]+\))?!?: \S[^\r\n]*$"
)
MAX_COMMIT_TITLE_LEN: Final = 72
MAX_PR_TITLE_LEN: Final = 80
PR_SECTIONS: Final = ("Why", "What", "How to Test")


class OutputFormatter:
    """Validate commit headers, PR titles, lengths, and mandatory sections."""

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
        """Return a Conventional Commits message or reject an invalid header / excessive length."""
        message = OutputFormatter._clean(raw_message)
        if not message:
            raise ValueError("Commit message cannot be empty.")
        
        first_line = message.splitlines()[0]
        if not re.fullmatch(COMMIT_PATTERN, first_line):
            raise ValueError("AI output must start with a Conventional Commits header.")
        
        if len(first_line) > MAX_COMMIT_TITLE_LEN:
            raise ValueError(
                f"Commit title exceeds maximum allowed length of {MAX_COMMIT_TITLE_LEN} chars "
                f"(current: {len(first_line)} chars)."
            )
        return message

    @staticmethod
    def format_pr(raw_pr: str) -> str:
        """Validate PR title length and preserve or enforce Why/What/How to Test sections with bullets."""
        description = OutputFormatter._clean(raw_pr)
        lines = description.splitlines()
        if not lines:
            raise ValueError("PR description cannot be empty.")

        # Validate or trim PR title if first line is a title
        first_line = lines[0].strip("# ").strip()
        if len(first_line) > MAX_PR_TITLE_LEN:
            # Enforce 80 char title limit
            lines[0] = first_line[:MAX_PR_TITLE_LEN]
            description = "\n".join(lines)

        # Enforce Why, What, How to Test sections
        for section in PR_SECTIONS:
            pattern = rf"(?im)^\s*#{{1,6}}\s+{re.escape(section)}\s*:?[ \t]*$"
            if not re.search(pattern, description):
                description += f"\n\n### {section}\n- Not provided; review required."

        return description.strip()
