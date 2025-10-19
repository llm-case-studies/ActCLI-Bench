"""
Terminal Wrapper - Intercepts stdin/stdout for AI CLI communication.

Wraps AI CLI terminals (claude, codex, gemini) and connects them to the
facilitator service for multi-AI communication.
"""

from .pty_wrapper import PTYWrapper
from .client import FacilitatorClient

__all__ = ["PTYWrapper", "FacilitatorClient"]
