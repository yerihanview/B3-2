"""Backward compatibility: re-export AIClient from git_agent.ai_client."""

from git_agent.ai_client import (
    AIClient,
    AIClientError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    ServerError,
)

__all__ = [
    "AIClient",
    "AIClientError",
    "AuthenticationError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
]
