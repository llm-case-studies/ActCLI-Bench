"""
actcli-shell - Multi-terminal TUI for AI communication.

Package init intentionally avoids importing heavy UI modules so that
lightweight utilities (e.g., SessionManager) can be used without
pulling optional dependencies like prompt_toolkit.
"""

__all__: list[str] = []
