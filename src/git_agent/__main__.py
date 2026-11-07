"""Entry point for python -m git_agent execution."""

import sys
from .cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
