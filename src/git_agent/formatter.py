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
HEADING_PATTERN: Final = r"^\s*(#{1,6})\s+(.+?)\s*:?\s*$"
BULLET_PATTERN: Final = r"^\s*[-*]\s+\S"
NOT_PROVIDED_BULLET: Final = "- Not provided; review required."
TRAILING_PUNCTUATION: Final = " ,;:-–—"


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
    def truncate_to_word_boundary(text: str, max_len: int = MAX_PR_TITLE_LEN) -> str:
        """Shorten text to at most max_len characters without cutting a word in half.

        The cut falls on the last whitespace inside the limit; only a single word
        longer than max_len is hard-cut, because no boundary exists there.
        """
        if max_len < 1:
            raise ValueError("max_len must be positive")
        collapsed = " ".join(text.split())
        if len(collapsed) <= max_len:
            return collapsed
        window = collapsed[: max_len + 1]
        boundary = window.rfind(" ")
        candidate = window[:boundary] if boundary > 0 else collapsed[:max_len]
        return candidate.rstrip(TRAILING_PUNCTUATION) or collapsed[:max_len]

    @staticmethod
    def _section_bodies(description: str) -> dict[str, list[str]]:
        """Map each Markdown heading (lower-cased) to the body lines beneath it.

        A body ends at the next heading of the same or a shallower level, so bullets
        written under a deeper sub-heading still belong to their parent section.
        """
        lines = description.splitlines()
        headings: list[tuple[int, int, str]] = []
        for index, line in enumerate(lines):
            match = re.match(HEADING_PATTERN, line)
            if match:
                headings.append((index, len(match.group(1)), match.group(2).strip().lower()))
        bodies: dict[str, list[str]] = {}
        for position, (index, level, name) in enumerate(headings):
            end = len(lines)
            for next_index, next_level, _next_name in headings[position + 1 :]:
                if next_level <= level:
                    end = next_index
                    break
            bodies[name] = [*bodies.get(name, []), *lines[index + 1 : end]]
        return bodies

    @staticmethod
    def _has_bullet(body: list[str]) -> bool:
        """Return whether a section body holds at least one '- ' or '* ' bullet with content."""
        return any(re.match(BULLET_PATTERN, line) for line in body)

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
        """Validate the PR title and require a bullet under every mandatory section."""
        description = OutputFormatter._clean(raw_pr)
        if not description:
            raise ValueError("PR description cannot be empty.")

        lines = description.splitlines()
        heading_title = lines[0].strip().lstrip("#").strip()
        if not heading_title:
            raise ValueError("PR title cannot be empty.")
        if lines[0].strip().startswith("#") and heading_title.lower() in {
            section.lower() for section in PR_SECTIONS
        }:
            raise ValueError(
                "PR title cannot be empty; the description must start with the PR title line."
            )
        if len(heading_title) > MAX_PR_TITLE_LEN:
            lines[0] = OutputFormatter.truncate_to_word_boundary(heading_title, MAX_PR_TITLE_LEN)
            description = "\n".join(lines)

        bodies = OutputFormatter._section_bodies(description)
        for section in PR_SECTIONS:
            body = bodies.get(section.lower())
            if body is None:
                description += f"\n\n### {section}\n{NOT_PROVIDED_BULLET}"
                continue
            if not OutputFormatter._has_bullet(body):
                raise ValueError(
                    f"PR section '{section}' must contain at least one bullet point (- or *)."
                )

        return description.strip()
