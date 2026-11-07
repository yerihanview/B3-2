"""CLI entry point: python -m src.main or python src/main.py [commit|pr] [OPTIONS]."""

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
DEFAULT_TEMPERATURE: Final = 0.2
DEFAULT_MAX_TOKENS: Final = 1000
COMMANDS: Final = ("commit", "pr")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse the optional subcommand, safe-mode switch, and parameter controls."""
    parser = argparse.ArgumentParser(
        description="Generate a commit message or PR description.",
        epilog=(
            "Examples: python src/main.py commit --staged | "
            "python src/main.py pr --dry-run | python src/main.py --pr"
        ),
    )
    parser.add_argument(
        "command", nargs="?", choices=COMMANDS, default=None, metavar="{commit,pr}",
        help="Optional subcommand: 'commit' (default) or 'pr'.",
    )
    parser.add_argument("--staged", action="store_true", help="Read staged changes.")
    parser.add_argument(
        "--pr", action="store_true", help="Generate Why/What/How to Test PR text (same as the 'pr' subcommand)."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview safe input without an API call.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model name.")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, help="Sampling temperature (0.0 to 2.0).")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Maximum completion tokens.")
    safety = parser.add_mutually_exclusive_group()
    safety.add_argument(
        "--safe-mode", dest="safe_mode", action="store_true", default=True,
        help="Mask sensitive data and truncate long diffs (default: on).",
    )
    safety.add_argument(
        "--no-safe-mode", dest="safe_mode", action="store_false",
        help="Send the raw diff without masking or truncation (use only on trusted input).",
    )
    namespace = parser.parse_args(args)
    namespace.pr = namespace.pr or namespace.command == "pr"
    return namespace


def _generate(args: argparse.Namespace, diff: str, status: str) -> str:
    """Preview protected inputs or generate and format the requested output."""
    client = AIClient(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        safe_mode=args.safe_mode,
    )
    if args.dry_run:
        return (
            f"Safe mode: {'on' if args.safe_mode else 'off'}\n"
            f"Parameters: model={args.model}, temp={args.temperature}, max_tokens={args.max_tokens}\n"
            f"Status:\n{client.prepare_input(status)}\n"
            f"Diff:\n{client.prepare_input(diff)}"
        )
    if args.pr:
        return OutputFormatter.format_pr(client.generate_pr_description(diff, status))
    return OutputFormatter.format_commit(client.generate_commit_message(diff, status))


def run_cli() -> int:
    """Print requested output and return a meaningful process exit code."""
    args = parse_args()
    if not args.safe_mode:
        print(
            "WARNING: Safe-Mode is off; the raw diff is sent to the API without masking or truncation.",
            file=sys.stderr,
        )
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
