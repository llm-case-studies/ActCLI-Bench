from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict


@dataclass
class LogManager:
    """Simple line-buffered log manager by category.

    Categories: events, errors, debug, output
    """

    max_lines: int = 2000
    buffers: Dict[str, Deque[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("events", "errors", "debug", "output", "troubleshooting"):
            self.buffers[name] = deque(maxlen=self.max_lines)

    def add(self, category: str, message: str) -> None:
        buf = self.buffers.setdefault(category, deque(maxlen=self.max_lines))
        for line in message.splitlines() or [message]:
            buf.append(line)

    def text(self, category: str) -> str:
        buf = self.buffers.get(category)
        if not buf:
            return ""
        return "\n".join(buf)
