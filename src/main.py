"""CLI entry point: python -m src.main or python src/main.py."""

import argparse
import sys
from typing import Final

if __package__:
    from .ai_client import AIClient
    from .formatter import OutputFormatter
    from .git_manager import GitManager
else:
    from ai_client import AIClient
    from formatter import OutputFormatter
    from git_manager import GitManager

EXIT_SUCCESS: Final = 0
EXIT_FAILURE: Final = 1
DEFAULT_MODEL: Final = "gpt-4o-mini"


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse supported CLI options with an injectable argument list."""
    parser = argparse.ArgumentParser(description="Generate a commit message or PR description.")
    parser.add_argument("--staged", action="store_true", help="Read staged changes.")
    parser.add_argument("--pr", action="store_true", help="Generate Why/What/How PR text.")
    parser.add_argument("--dry-run", action="store_true", help="Preview safe input without an API call.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model name.")
    return parser.parse_args(args)


def _generate(args: argparse.Namespace, diff: str, status: str) -> str:
    """Preview protected inputs or generate and format the requested output."""
    client = AIClient(model=args.model)
    if args.dry_run:
        safe_status = client.truncate_diff(client.mask_sensitive_data(status))
        safe_diff = client.truncate_diff(client.mask_sensitive_data(diff))
        return f"Status:\n{safe_status}\nDiff:\n{safe_diff}"
    if args.pr:
        return OutputFormatter.format_pr(client.generate_pr_description(diff, status))
    return OutputFormatter.format_commit(client.generate_commit_message(diff, status))


def run_cli() -> int:
    """Print requested output and return a meaningful process exit code."""
    args = parse_args()
    manager = GitManager()
    try:
        if not manager.is_git_repo():
            raise RuntimeError("Run this command inside a Git working tree.")
        status = manager.get_status()
        diff = manager.get_diff(staged=args.staged)
        if not diff.strip():
            print("No changes in the selected diff. Stage new files with git add first.")
            return EXIT_SUCCESS
        print(_generate(args, diff, status))
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(run_cli())
