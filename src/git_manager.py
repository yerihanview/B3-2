"""Backward compatibility: re-export GitManager from git_agent.git_manager."""

from git_agent.git_manager import GitManager

__all__ = ["GitManager"]
