"""TerminalProbeResponder -- replies to terminal probe requests like ESC[6n."""

from __future__ import annotations

from typing import Optional


class TerminalProbeResponder:
    """Builds responses for terminal probe requests.

    Detects DSR (ESC[6n) and similar terminal queries and computes
    appropriate responses using the emulator's current state.
    """

    def response_for_text(self, text: str, emulator) -> Optional[str]:
        """Return a response string for a terminal probe, or None.

        Args:
            text: The text being sent to the terminal (checked for probes).
            emulator: An EmulatedTerminal-like object with ``mode`` and
                ``_screen.cursor`` attributes.

        Returns:
            An escape-sequence response string, or ``None`` if no probe
            was detected or no response is possible.
        """
        if "\x1b[6n" not in text:
            return None

        if getattr(emulator, "mode", None) != "pyte":
            return None

        screen = getattr(emulator, "_screen", None)
        if screen is None:
            return None

        cursor = getattr(screen, "cursor", None)
        if cursor is None:
            return None

        row = getattr(cursor, "y", 0) + 1
        col = getattr(cursor, "x", 0) + 1
        return f"\x1b[{row};{col}R"
