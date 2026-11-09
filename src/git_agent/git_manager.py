"""Read Git state without invoking a shell or modifying the repository."""

from __future__ import annotations

import subprocess
from typing import Final

GIT_TIMEOUT: Final = 10


class GitManager:
    """Collect information from the current working directory's repository."""

    def _run(self, arguments: list[str]) -> str:
        """Execute a bounded Git command, hiding potentially sensitive stderr."""
        try:
            result = subprocess.run(
                ["git", *arguments], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT,
                check=True, shell=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError("Git command failed; check repository and Git installation.") from error
        return result.stdout

    def is_git_repo(self) -> bool:
        """Return whether the current directory belongs to a Git work tree."""
        try:
            return self._run(["rev-parse", "--is-inside-work-tree"]).strip() == "true"
        except RuntimeError:
            return False

    def get_status(self) -> str:
        """Return porcelain status, including untracked paths."""
        return self._run(["status", "--porcelain=v1"])

    def get_diff(self, staged: bool = False) -> str:
        """Return staged or unstaged tracked changes without external diff tools."""
        arguments = ["diff", "--no-ext-diff", "--no-textconv", "--no-color"]
        if staged:
            arguments.append("--cached")
        return self._run([*arguments, "--"])
