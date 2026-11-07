"""Root CLI entrypoint forwarding to src.main:run_cli."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.main import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
