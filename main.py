"""Root CLI entrypoint forwarding to git_agent.cli:run_cli."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from git_agent.cli import run_cli, main

__all__ = ["run_cli", "main"]

if __name__ == "__main__":
    sys.exit(run_cli())
