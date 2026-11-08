"""CLI implementation for git_agent package: supports commit and pr subcommands."""

import argparse
import os
import sys
from typing import Final

from .ai_client import AIClient
from .formatter import OutputFormatter
from .git_manager import GitManager

EXIT_SUCCESS: Final = 0
EXIT_FAILURE: Final = 1
DEFAULT_MODEL: Final = "gpt-4o-mini"
DEFAULT_TEMPERATURE: Final = 0.2
DEFAULT_MAX_TOKENS: Final = 1000
COMMANDS: Final = ("commit", "pr")


def load_dotenv(dotenv_path: str = ".env") -> None:
    """Read a local .env file and populate os.environ without third-party dependencies."""
    if not os.path.exists(dotenv_path):
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse the optional subcommand, safe-mode switch, and parameter controls."""
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="git-agent",
        description="Generate a commit message or PR description.",
        epilog=(
            "Examples:\n"
            "  python -m git_agent commit --staged\n"
            "  python -m git_agent pr --dry-run\n"
            "  git-agent commit\n"
            "  python main.py commit"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    parser.add_argument(
        "--api-base", default=os.getenv("OPENAI_BASE_URL") or os.getenv("AI_API_BASE_URL"),
        help="Custom API base URL (e.g. https://copa.codyssey.kr/v1).",
    )
    parser.add_argument("--model", default=os.getenv("AI_MODEL", DEFAULT_MODEL), help="AI model name.")
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
    """Preview protected inputs or generate and format the requested output with section delimiters."""
    client = AIClient(
        base_url=getattr(args, "api_base", None),
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        safe_mode=args.safe_mode,
    )
    if args.dry_run:
        return (
            "--- Dry Run Preview ---\n"
            f"Safe mode: {'on' if args.safe_mode else 'off'}\n"
            f"Parameters: model={args.model}, temp={args.temperature}, max_tokens={args.max_tokens}\n"
            f"Status:\n{client.prepare_input(status)}\n"
            f"Diff:\n{client.prepare_input(diff)}\n"
            "-----------------------"
        )
    if args.pr:
        formatted = OutputFormatter.format_pr(client.generate_pr_description(diff, status))
        lines = formatted.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        return (
            "--- PR Title ---\n"
            f"{title}\n\n"
            "--- PR Body ---\n"
            f"{body}\n"
            "---------------"
        )
    formatted = OutputFormatter.format_commit(client.generate_commit_message(diff, status))
    return (
        "--- Commit Message ---\n"
        f"{formatted}\n"
        "----------------------"
    )


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
            untracked = [line[3:].strip() for line in status.splitlines() if line.startswith("?? ")]
            if untracked:
                print(
                    "No changes in the selected diff, but untracked files were detected:\n"
                    + "\n".join(f"  ? {path}" for path in untracked)
                    + "\nPlease stage new files with 'git add <file>' first."
                )
            else:
                print("No changes in the selected diff. Stage new files with git add first.")
            return EXIT_SUCCESS
        print(_generate(args, diff, status))
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_FAILURE
    return EXIT_SUCCESS


def main() -> None:
    """Console script entry point terminating the process with run_cli's exit code."""
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
