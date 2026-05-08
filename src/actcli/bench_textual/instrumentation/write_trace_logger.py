"""WriteTraceLogger -- reusable PTY write tracing with configurable sinks."""

from __future__ import annotations

import os
from typing import Callable, List, Optional


class FileTraceSink:
    """Appends write-trace lines to a file (best-effort)."""

    def __init__(self, path: str) -> None:
        self._path = path

    def record(self, name: str, data: str) -> None:
        try:
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(f"{name}: {repr(data)}\n")
        except Exception:
            pass


class MemoryTraceSink:
    """Collects trace records in memory."""

    def __init__(self) -> None:
        self.records: List[str] = []

    def record(self, name: str, data: str) -> None:
        self.records.append(f"{name}: {repr(data)}")


class CallbackTraceSink:
    """Forwards formatted trace lines to a callback."""

    def __init__(self, callback: Callable[[str], None]) -> None:
        self._callback = callback

    def record(self, name: str, data: str) -> None:
        try:
            self._callback(f"{name}: {repr(data)}")
        except Exception:
            pass


class WriteTraceLogger:
    """Logs PTY write traces to configurable sinks.

    Sinks are called sequentially for each ``record()`` call.
    The file sink is enabled via ``ACTCLI_WRITE_TRACE=1`` env var.
    """

    DEFAULT_TRACE_PATH = "docs/Trouble-Snaps/write_debug.log"

    def __init__(
        self, name: str, sinks: Optional[List[FileTraceSink | MemoryTraceSink | CallbackTraceSink]] = None
    ) -> None:
        self.name = name
        self.sinks: List[FileTraceSink | MemoryTraceSink | CallbackTraceSink] = (
            sinks if sinks is not None else []
        )

    def record(self, data: str) -> None:
        for sink in self.sinks:
            sink.record(self.name, data)

    @classmethod
    def from_env(cls, name: str) -> "WriteTraceLogger":
        sinks: List[FileTraceSink | MemoryTraceSink | CallbackTraceSink] = []
        env_val = os.environ.get("ACTCLI_WRITE_TRACE", "")
        if env_val == "1":
            sinks.append(FileTraceSink(cls.DEFAULT_TRACE_PATH))
        return cls(name, sinks)
