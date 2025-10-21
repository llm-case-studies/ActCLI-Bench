"""Textual-based bench for wrapping terminals and facilitating KT.

Goals:
- Keep terminals behaving like standalone CLIs (VSCode-style integrated terminal)
- Provide a minimal, mouse-first Control Pad to broadcast prompts to
  all unmuted terminals (raw injection to stdin)
- Auto-start a local facilitator and create a session; optionally
  mirror broadcast prompts to the facilitator (so the browser viewer
  reflects control prompts)
- Preserve theme switching (F1/F2/F3)
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Static,
    Input,
    Button,
    Log,
    Checkbox,
    Label,
    Tree,
)

from dataclasses import dataclass
from typing import Dict, Optional, List
import shlex
import re
from importlib import metadata
from pathlib import Path
from functools import lru_cache
from datetime import datetime
from textual.timer import Timer

from ..wrapper_tui.session_manager import SessionManager
from ..wrapper.client import FacilitatorClient
from .terminal_runner import TerminalRunner
from .term_emulator import EmulatedTerminal
from .term_view import TermView
from .log_manager import LogManager
from .terminal_manager import TerminalManager
from .diagnostics import DiagnosticsManager


THEME_CLASSES = ("theme-ledger", "theme-analyst", "theme-seminar")


@dataclass
class TerminalItem:
    name: str
    command: List[str]
    runner: TerminalRunner
    muted: bool = True


class BenchTextualApp(App):
    CSS_PATH = "themes.tcss"

    BINDINGS = [
        Binding("f1", "switch_theme('ledger')", "Ledger"),
        Binding("f2", "switch_theme('analyst')", "Analyst"),
        Binding("f3", "switch_theme('seminar')", "Seminar"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Ensure core attributes exist before mount/compose triggers any status updates
        self.session_manager = SessionManager()
        self.log_manager = LogManager()

        # Terminal management (replaces scattered dictionaries)
        self.terminal_manager = TerminalManager(
            debug_logger=self._debug_logger,
            log_manager=self.log_manager,
            max_scrollback_lines=2000,
            on_output_callback=self._on_terminal_output
        )

        # Version info (will be populated in on_mount)
        self._version_info: Dict[str, str] = {}

        # Diagnostics manager
        self.diagnostics = DiagnosticsManager(
            terminal_manager=self.terminal_manager,
            log_manager=self.log_manager,
            version_info=self._version_info,
            get_app_state=self._get_app_state_for_diagnostics
        )

        # UI state
        self.viewer_url: Optional[str] = None
        self.facilitator_client: Optional[FacilitatorClient] = None
        self.active_view: str = "terminal"
        self.active_terminal: Optional[str] = None  # Currently selected terminal
        self.mirror_to_facilitator: bool = False
        self.last_broadcast: Optional[str] = None
        self.adding_mode: bool = False
        self.connect_mode: bool = False
        self.action_lines: List[str] = []
        self._session_id: Optional[str] = None
        self._writer_attached: bool = False
        self._border_blink_timer: Optional[Timer] = None

        # Scrollback UI state (managed separately from TerminalManager)
        self.scroll_offsets: Dict[str, int] = {}

    async def on_mount(self) -> None:
        # Start with the first palette
        self.add_class("theme-ledger")
        # App state
        # Ensure version info is gathered once mount occurs (may refresh from __init__ placeholder)
        self._version_info = self._gather_version_info()
        self._update_status_line()
        # Configure terminal view interactions
        self.terminal_view.set_writer(self._write_to_active)
        self.terminal_view.set_navigator(self._on_navigate)
        self.terminal_view.set_size_listener(self._on_terminal_view_size_change)
        self.terminal_view.set_key_logger(self._record_key_event)
        self._writer_attached = True
        self._start_border_blink(duration=1.2)
        self._start_border_blink()
        # Kick off session bootstrap
        await self._bootstrap_session_async()
        # Session bootstrap may update status text, refresh afterwards
        self._update_status_line()
        # Build nav tree after state is ready
        try:
            self._rebuild_nav_tree()
        except Exception:
            pass
        # Set up terminal view focus callback to refresh cursor display
        self.terminal_view.set_on_focus(self._on_terminal_view_focused)

    def compose(self) -> ComposeResult:
        yield Header(id="header")

        # Main split: left navigation + right detail
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("ActCLI • Bench", id="brand")
                # Tree navigation
                self.nav_tree = Tree("Navigation", id="nav-tree")
                yield self.nav_tree
                yield Static("F1: Ledger • F2: Analyst • F3: Seminar", id="hint")

            with Vertical(id="detail"):
                # Right: Title / status line
                self.status_line = Static("Terminal", id="title")
                yield self.status_line
                # Active terminal output view (emulated, focusable)
                self.terminal_view = TermView(id="terminal-view", expand=True, shrink=False)
                yield self.terminal_view
                # Control pad
                with Horizontal(id="control"):
                    self.control_input = Input(placeholder="Broadcast to all unmuted…", id="control-input")
                    yield self.control_input
                    self.btn_broadcast = Button("Broadcast", id="btn-broadcast")
                    yield self.btn_broadcast
                    self.chk_mirror = Checkbox("Mirror to viewer", id="chk-mirror")
                    yield self.chk_mirror

        yield Footer(id="footer")

    def action_switch_theme(self, theme: str) -> None:
        # Remove previous theme classes and apply the new one
        for cls in THEME_CLASSES:
            self.remove_class(cls)
        self.add_class(f"theme-{theme}")
        self._log(f"Switched theme → {theme}")

    def on_resize(self, event) -> None:  # type: ignore[override]
        try:
            if self.active_view == "terminal" and self.active_terminal:
                name = self.active_terminal
                self._sync_terminal_size(name)
                self._schedule_terminal_resizes(name)
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[attr-defined]
        # Only the control pad input triggers submission here
        if event.input is self.control_input:
            text = event.value.strip()
            if not text:
                return
            if self.adding_mode:
                self._handle_add_from_text(text)
            elif self.connect_mode:
                self._handle_connect_from_text(text)
            else:
                self._handle_broadcast(text)
            event.input.value = ""

    # Helper to write a line regardless of Log/RichLog API differences
    def _log(self, message: str) -> None:
        # Route general bench messages to the actions log
        self._log_action(message)

    def _debug_logger(self, message: str) -> None:
        """Logger callback for terminal emulator debug output."""
        self.log_manager.add("debug", message)

    def _get_app_state_for_diagnostics(self) -> Dict[str, any]:
        """Get current app state for diagnostics snapshot.

        Returns:
            Dictionary with active_view, active_terminal, writer_attached
        """
        return {
            "active_view": self.active_view,
            "active_terminal": self.active_terminal,
            "writer_attached": self._writer_attached
        }

    def _gather_version_info(self) -> Dict[str, str]:
        """Collect version metadata for status banner."""
        return {
            "bench": self._get_package_version(["actcli-bench", "actcli"], default="dev"),
            "textual": self._get_package_version(["textual"], default="unknown"),
            "pyte": self._get_package_version(["pyte"], default="none"),
        }

    def _get_package_version(self, names: List[str], default: str) -> str:
        for pkg in names:
            try:
                return metadata.version(pkg)
            except Exception:
                if pkg == "actcli-bench":
                    fb = self._fallback_bench_version()
                    if fb:
                        return fb
                continue
        return default

    @staticmethod
    @lru_cache(maxsize=1)
    def _fallback_bench_version() -> Optional[str]:
        """Read actcli-bench version directly from pyproject when metadata is missing."""
        try:
            pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
            text = pyproject.read_text(encoding="utf-8")
        except Exception:
            return None
        match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if match:
            return match.group(1)
        return None

    def _current_emulator_mode(self) -> str:
        emulators_obj = getattr(self, "emulators", {}) or {}
        if not isinstance(emulators_obj, dict):
            self._log_action(f"Unexpected emulators container type: {type(emulators_obj)!r}")
            emulators_obj = {}
        emulators = emulators_obj
        active = getattr(self, "active_terminal", None)
        def _resolve_mode(candidate, label: str) -> Optional[str]:
            if candidate is None:
                return None
            try:
                mode_val = getattr(candidate, "mode")
                if callable(mode_val):
                    mode_val = mode_val()
            except Exception as exc:
                self._log_action(f"Mode lookup failed for {label}: {exc}")
                return None
            return str(mode_val) if isinstance(mode_val, str) else None

        if active and active in emulators:
            mode_active = _resolve_mode(emulators.get(active), active)
            if mode_active:
                return mode_active
        for name, emu_candidate in emulators.items():
            mode_candidate = _resolve_mode(emu_candidate, name)
            if mode_candidate:
                return mode_candidate
        return "plain"

    def _update_status_line(self) -> None:
        status = getattr(self, "status_line", None)
        if not status:
            return
        session_val = getattr(self, "_session_id", None) or "(none)"
        viewer_val = getattr(self, "viewer_url", None) or "(none)"
        try:
            versions_obj = getattr(self, "_version_info", None)
            if not isinstance(versions_obj, dict):
                if versions_obj is not None:
                    self._log_action(f"Unexpected version info type: {type(versions_obj)!r}")
                versions_obj = {}
            versions = versions_obj
            bench_v = str(versions.get("bench", "dev"))
            textual_v = str(versions.get("textual", "unknown"))
            pyte_v = str(versions.get("pyte", "none"))
        except Exception as exc:
            self._log_action(f"Version info retrieval failed: {exc}")
            bench_v = "dev"
            textual_v = "unknown"
            pyte_v = "none"
        try:
            mode = self._current_emulator_mode()
        except Exception as exc:
            mode = "plain"
            self._log_action(f"Mode detection failed: {exc}")
        try:
            status.update(
                "Terminal  |  "
                f"Session: {session_val}  |  "
                f"Viewer: {viewer_val}  |  "
                f"actcli-bench {bench_v}  |  "
                f"textual {textual_v}  |  "
                f"pyte {pyte_v}  |  "
                f"mode <{mode}>"
            )
        except Exception as exc:
            self._log_action(f"Status line update failed: {exc}")

    def _start_border_blink(self, duration: float = 1.0) -> None:
        view = getattr(self, "terminal_view", None)
        if not view:
            return
        try:
            view.add_class("blink-border")
        except Exception:
            return
        if self._border_blink_timer is not None:
            try:
                self._border_blink_timer.stop()
            except Exception:
                pass
            self._border_blink_timer = None

        def _clear_border() -> None:
            try:
                view.remove_class("blink-border")
            except Exception:
                pass
            self._border_blink_timer = None

        try:
            self._border_blink_timer = self.set_timer(duration, _clear_border)
        except Exception:
            _clear_border()

    def _troubleshooting_snapshot(self) -> str:
        """Generate troubleshooting snapshot - delegates to DiagnosticsManager."""
        return self.diagnostics.generate_snapshot()

    def _update_troubleshooting_log(self) -> str:
        """Update troubleshooting log - delegates to DiagnosticsManager."""
        return self.diagnostics.update_troubleshooting_log()

    def _export_troubleshooting_pack(self) -> None:
        """Export troubleshooting pack to file - delegates to DiagnosticsManager."""
        result = self.diagnostics.export_to_file()
        if result:
            self._log_action(f"Troubleshooting pack saved → {result}")
        else:
            self._log_action("Troubleshooting pack export failed")

    def _record_key_event(self, key: str, character: Optional[str], modifiers: set[str]) -> None:
        """Record key event for diagnostics - delegates to DiagnosticsManager."""
        self.diagnostics.record_key_event(key, character, modifiers)
        entry = f"key={key!r} char={character!r} mods={sorted(modifiers)} writer={self._writer_attached}"
        self._debug_logger(f"KEY event: {entry}")

    def _log_emulator_mode(self, term_name: str, emulator: EmulatedTerminal) -> None:
        """Emit a one-time log entry describing emulator mode."""
        if term_name in self._emulator_mode_logged:
            return
        self._emulator_mode_logged.add(term_name)
        if emulator.mode == "pyte":
            version = emulator.pyte_version or "unknown"
            if self._version_info.get("pyte") in ("none", "unknown"):
                self._version_info["pyte"] = version
            msg = f"EmulatedTerminal: using pyte {version}"
        else:
            msg = "EmulatedTerminal: pyte not available -- falling back to plain (install pyte)"
            # Ensure banner reflects absence
            self._version_info["pyte"] = "none"
        self._log_action(f"[{term_name}] {msg}")
        self._update_status_line()

    def _sync_terminal_size(self, name: str) -> None:
        """Sync terminal view size to both emulator and PTY child process."""
        if name not in self.terminal_manager.terminals:
            return

        view = getattr(self, "terminal_view", None)
        if not view:
            return

        # Get pane size from Textual
        content_region = getattr(view, "content_region", None)
        if content_region is not None:
            cols = content_region.width
            rows = content_region.height
        else:
            cols = view.content_size.width
            rows = view.content_size.height

        if cols <= 0 or rows <= 0:
            return

        # Delegate to TerminalManager
        self.terminal_manager.sync_terminal_size(name, cols, rows)

    def _schedule_terminal_resizes(self, name: str) -> None:
        """Schedule delayed syncs to catch late layout adjustments."""
        delays = (0.05, 0.2, 0.5, 1.0)
        try:
            self.call_after_refresh(lambda n=name: self._sync_terminal_size(n))
        except Exception:
            pass
        for delay in delays:
            try:
                self.set_timer(delay, lambda n=name: self._sync_terminal_size(n))
            except Exception:
                pass

    def _on_terminal_view_size_change(self) -> None:
        """Handle terminal view size updates by syncing the active terminal."""
        if self.active_terminal:
            self._schedule_terminal_resizes(self.active_terminal)

    def _resize_emulator_if_needed(self, emu: EmulatedTerminal) -> None:
        """Resize emulator to match terminal view content area."""
        view = getattr(self, "terminal_view", None)
        if not view:
            self._debug_logger("Resize skipped: no terminal_view")
            return

        # Debug: log all available size attributes
        attrs_to_check = ["size", "region", "content_size", "container_size", "virtual_size"]
        for attr in attrs_to_check:
            if hasattr(view, attr):
                val = getattr(view, attr)
                self._debug_logger(f"view.{attr} = {val}")

        # Textual's layout already accounts for borders and padding in content_size.
        # If content_region is available (newer Textual), prefer that so we always
        # operate on the actual renderable cell area.
        content_region = getattr(view, "content_region", None)
        if content_region is not None:
            content_width = content_region.width
            content_height = content_region.height
            self._debug_logger(
                f"Using content_region: {content_width}x{content_height}"
            )
        else:
            content_width = view.content_size.width
            content_height = view.content_size.height
            self._debug_logger(
                f"Using content_size: {content_width}x{content_height}"
            )

        if content_width <= 0 or content_height <= 0:
            self._debug_logger(f"Resize skipped: invalid content size {content_width}x{content_height}")
            return

        if emu.cols != content_width or emu.rows != content_height:
            old_size = f"{emu.cols}x{emu.rows}"
            emu.resize(content_width, content_height)
            self._debug_logger(f"Resized emulator from {old_size} to {content_width}x{content_height}")

    def _set_terminal_text(self, text: str) -> None:
        view = getattr(self, "terminal_view", None)
        if view:
            try:
                # Debug: log what we're about to display
                lines = text.split('\n')
                if lines:
                    first_line = lines[0] if lines else ""
                    self._debug_logger(f"Setting text: {len(lines)} lines, first line len={len(first_line)}, preview={repr(first_line[:100])}")
                view.update(text)
            except Exception as e:
                self._debug_logger(f"Error updating view: {e}")

    def _log_action(self, message: str) -> None:
        # Always mirror to events category; compact sidebar writer is optional
        self.action_lines.append(message)
        try:
            self.log_manager.add("events", message)
        except Exception:
            pass
        alog = getattr(self, "actions_log", None)
        if alog:
            try:
                if hasattr(alog, "write"):
                    alog.write(message)
                else:
                    alog.write_line(message)
            except Exception:
                pass
        # If viewing Events in right pane, refresh it
        if getattr(self, "active_view", "") == "log:events":
            self._set_terminal_text(self.log_manager.text("events"))


    # --- Internal helpers -------------------------------------------------

    def _on_terminal_exit(self, name: str, exit_code: int) -> None:
        """Log terminal exit status to Events."""
        msg = f"Terminal '{name}' exited (code {exit_code})"
        self._log_action(msg)

    def _on_terminal_view_focused(self) -> None:
        """Called when terminal view gains focus - refresh display with cursor."""
        if self.active_terminal:
            state = self.terminal_manager.get_terminal_state(self.active_terminal)
            if state:
                emu = state.emulator
                # Resize emulator to match terminal view if needed
                self._resize_emulator_if_needed(emu)
                self._set_terminal_text(emu.text_with_cursor(show=True))

    def _on_terminal_output(self, name: str, text: str) -> None:
        """Called when terminal output arrives - refresh view if needed.

        TerminalManager handles emulator feeding and logging, this just updates the UI.
        """
        # Refresh terminal view if this is the active terminal and we're in terminal view
        if self.active_terminal == name and self.active_view == "terminal":
            state = self.terminal_manager.get_terminal_state(name)
            if state and state.scroll_offset == 0:
                # Only refresh if not scrolled away
                # Show cursor when in terminal view and not scrolled away
                self._set_terminal_text(state.emulator.text_with_cursor(show=self.terminal_view.has_focus))

    def _is_control_sequence(self, s: str) -> bool:
        t = s.strip()
        if not t:
            return True
        if re.search(r"[<M]\d+;\d+;\d+[Mm]", s):
            return True
        if re.search(r"\x1B\[<\d+;\d+;\d+[Mm]", s):
            return True
        if re.match(r"^\](\d+);", s):
            return True
        if re.search(r"\x1B\[[\d;?]*[A-Za-z<>]", s):
            return True
        if re.search(r"\?\[\??\d+[hl]", s):
            return True
        if re.search(r"\?\[[\d;]*[A-HJKSTfmnsur]", s):
            return True
        if "cursor position could not be read" in s.lower():
            return True
        if re.match(r"^[M<\d;]+[Mm]", s) and s.count(";") >= 2:
            return True
        return False

    async def _bootstrap_session_async(self) -> None:
        """Start facilitator and create a default session in the background."""
        ok = await self.session_manager.start_local_facilitator()
        if not ok:
            self._log("Failed to start facilitator")
            self._log_action("Facilitator start failed")
            return
        ok = await self.session_manager.create_default_session()
        if not ok or not self.session_manager.session:
            self._log_action("Default session creation failed — continuing without facilitator viewer")
            return

        try:
            sid = getattr(self.session_manager.session, "session_id", None)
            if not sid:
                raise RuntimeError("session missing after creation")
            self.viewer_url = f"{self.session_manager.facilitator_url}/viewer/{sid}"
            try:
                self._set_title_status(sid)
            except Exception as exc:
                self._log_action(f"Session status update failed: {exc}")
            # Connect as moderator (optional mirror)
            self.facilitator_client = FacilitatorClient(self.session_manager.facilitator_url)
            try:
                await self.facilitator_client.join_session(sid, "moderator", participant_type="human")
                await self.facilitator_client.connect_websocket()
            except Exception as exc:
                self.facilitator_client = None
                self._log_action(f"Moderator WS connect failed (mirror disabled): {exc}")
        except Exception as exc:
            self._log_action(f"Session bootstrap error: {exc}")
            return

    def _set_title_status(self, session_id: Optional[str]) -> None:
        self._session_id = session_id
        self._update_status_line()

    def _handle_broadcast(self, text: str) -> None:
        """Broadcast a line to all unmuted terminals; optionally mirror to viewer."""
        self.last_broadcast = text
        # Inject into each unmuted terminal
        for name in self.terminal_manager.list_terminals():
            state = self.terminal_manager.get_terminal_state(name)
            if state and not state.item.muted:
                state.item.write(text)
        # Mirror to facilitator feed if enabled
        if self.chk_mirror.value and self.facilitator_client and self.session_manager.session:
            import asyncio
            try:
                asyncio.create_task(self.facilitator_client.send_message(text, to="all", msg_type="chat"))
            except Exception:
                pass

    # --- Actions / Events -------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[attr-defined]
        bid = event.button.id or ""
        if bid == "btn-broadcast":
            text = self.control_input.value.strip()
            if text:
                if self.adding_mode:
                    self._handle_add_from_text(text)
                elif self.connect_mode:
                    self._handle_connect_from_text(text)
                else:
                    self._handle_broadcast(text)
                self.control_input.value = ""

    # --- UI helpers -------------------------------------------------------

    def _handle_add_from_text(self, text: str) -> None:
        # Use shell-like parsing so quotes are respected
        try:
            parts = shlex.split(text)
        except Exception:
            parts = text.split()
        if not parts:
            return
        if len(parts) == 1:
            name = parts[0]
            cmd = [parts[0]]
        else:
            name = parts[0]
            cmd = parts[1:]
        self._add_terminal(name, cmd)
        # Exit add mode
        self.adding_mode = False
        self.control_input.placeholder = "Broadcast to all unmuted…"

    def _handle_connect_from_text(self, text: str) -> None:
        session_id = text.strip()
        if not session_id:
            return
        import asyncio
        asyncio.create_task(self._connect_session_async(session_id))
        # Exit connect mode
        self.connect_mode = False
        self.control_input.placeholder = "Broadcast to all unmuted…"

    async def _connect_session_async(self, session_id: str) -> None:
        try:
            ok = await self.session_manager.join_session(session_id, "moderator")
            if ok:
                self.viewer_url = f"{self.session_manager.facilitator_url}/viewer/{session_id}"
                self._set_title_status(session_id)
                self._log_action(f"Connected to session: {session_id}")
                # Ensure facilitator_client is connected for mirror
                if not self.facilitator_client:
                    self.facilitator_client = FacilitatorClient(self.session_manager.facilitator_url)
                try:
                    await self.facilitator_client.join_session(session_id, "moderator", participant_type="human")
                    await self.facilitator_client.connect_websocket()
                except Exception:
                    pass
            else:
                self._log_action(f"Failed to connect session: {session_id}")
        except Exception as e:
            self._log_action(f"Connect error for {session_id}: {e}")

    def _add_terminal(self, name: str, cmd: List[str]) -> None:
        # Use TerminalManager to create and start terminal
        success = self.terminal_manager.add_terminal(name, cmd)

        if not success:
            self._log(f"Failed to start: {' '.join(cmd)}")
            self._log_action(f"Start failed for {name}: {' '.join(cmd)}")
            return

        # Set as active terminal
        self.active_terminal = name

        # Set initial PTY size (critical - do this right after starting!)
        self._sync_terminal_size(name)
        self._schedule_terminal_resizes(name)

        # Initialize UI-specific state
        self.scroll_offsets[name] = 0

        self._switch_view("tab-terminal")
        self._update_status_line()
        self._refresh_nav()
        self._set_terminal_text(f"Added terminal '{name}' → {' '.join(cmd)}  [muted]")
        self._log_action(f"Added: {name} cmd={' '.join(cmd)} [muted]")

    # --- View switching -------------------------------------------------
    def _switch_view(self, tab_id: str) -> None:
        if tab_id == "tab-terminal":
            self.active_view = "terminal"
            self.terminal_view.set_writer(self._write_to_active)
            self.terminal_view.focus()
            name = self.active_terminal
            text = ""
            if name:
                state = self.terminal_manager.get_terminal_state(name)
                if state:
                    # Show cursor immediately since we just focused
                    text = state.emulator.text_with_cursor(show=True)
            self._set_terminal_text(text)
            self._writer_attached = True
            self._start_border_blink()
            return

        # Logs view
        self.terminal_view.set_writer(None)
        self._writer_attached = False
        mapping = {
            "tab-events": "events",
            "tab-errors": "errors",
            "tab-output": "output",
            "tab-debug": "debug",
            "tab-troubleshooting": "troubleshooting",
        }
        cat = mapping.get(tab_id, "events")
        self.active_view = f"log:{cat}"
        if cat == "troubleshooting":
            text = self._update_troubleshooting_log()
            self._start_border_blink(duration=1.5)
        else:
            text = self.log_manager.text(cat)
        if not text:
            text = f"(no {cat})"
        self._set_terminal_text(text)

    # Write bytes/strings to the active terminal's PTY
    def _write_to_active(self, data: str) -> None:
        name = self.active_terminal
        if not name or name == "__logs__":
            return
        state = self.terminal_manager.get_terminal_state(name)
        if not state:
            return
        try:
            self._debug_logger(f"KEY→PTY [{name}]: {repr(data)}")
            state.item.write(data)
        except Exception:
            pass

    def _refresh_nav(self) -> None:
        self._rebuild_nav_tree()

    # --- Tree nav ------------------------------------------------------
    def _rebuild_nav_tree(self) -> None:
        # Clear existing children in a way compatible with Textual 6.x
        try:
            for child in list(self.nav_tree.root.children):
                try:
                    child.remove()
                except Exception:
                    pass
        except Exception:
            pass
        terminals_node = self.nav_tree.root.add("Terminals")
        # Add action
        add_node = terminals_node.add("+ Add…")
        add_node.data = {"type": "add_terminal"}
        for name in self.terminal_manager.list_terminals():
            state = self.terminal_manager.get_terminal_state(name)
            if state:
                mark = "[M]" if state.item.muted else "[U]"
                node = terminals_node.add(f"{name} {mark}")
                node.data = {"type": "terminal", "name": name}
        sessions_node = self.nav_tree.root.add("Sessions")
        cur = sessions_node.add("Current session")
        cur.data = {"type": "session_info"}
        connect = sessions_node.add("Connect…")
        connect.data = {"type": "connect"}
        settings_node = self.nav_tree.root.add("Settings")
        m_all = settings_node.add("Mute All")
        m_all.data = {"type": "action", "id": "mute_all"}
        u_all = settings_node.add("Unmute All")
        u_all.data = {"type": "action", "id": "unmute_all"}
        # Build mirror toggle label safely even if chk_mirror isn't created yet
        mirror_checked = False
        try:
            mirror_checked = bool(self.chk_mirror.value)
        except Exception:
            mirror_checked = False
        mirror_label = f"Mirror to viewer {'[X]' if mirror_checked else '[ ]'}"
        mirror = settings_node.add(mirror_label)
        mirror.data = {"type": "action", "id": "toggle_mirror"}
        export_pack = settings_node.add("Export troubleshooting pack")
        export_pack.data = {"type": "action", "id": "export_troubleshooting"}
        logs_node = self.nav_tree.root.add("Logs")
        for cat in ("Events", "Errors", "Output", "Debug"):
            n = logs_node.add(cat)
            n.data = {"type": "log", "cat": cat.lower()}
        tpack = logs_node.add("Troubleshooting Pack")
        tpack.data = {"type": "log", "cat": "troubleshooting"}
        tpack_save = tpack.add("Save to file")
        tpack_save.data = {"type": "action", "id": "export_troubleshooting"}
        self.nav_tree.root.expand()
        terminals_node.expand()
        sessions_node.expand()
        settings_node.expand()
        logs_node.expand()
        tpack.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:  # type: ignore[attr-defined]
        data = getattr(event.node, "data", None) or {}
        t = data.get("type")
        if t == "add_terminal":
            # Switch control input into Add mode
            self.adding_mode = True
            self.connect_mode = False
            self.control_input.placeholder = "Add terminal: <name> <command...>  (e.g., CO gemini)"
            self.control_input.value = ""
            self.control_input.focus()
        elif t == "terminal":
            name = data.get("name")
            state = self.terminal_manager.get_terminal_state(name)
            if state:
                self.active_terminal = name
                self._update_status_line()
                self.active_view = "terminal"
                self.terminal_view.set_writer(self._write_to_active)
                self.terminal_view.set_navigator(self._on_navigate)
                self.terminal_view.focus()
                # Sync terminal size to both emulator and PTY
                self._sync_terminal_size(name)
                # Also sync again after first render to capture final content size
                try:
                    self.call_after_refresh(lambda n=name: self._sync_terminal_size(n))
                except Exception:
                    pass
                self._schedule_terminal_resizes(name)
                self._set_terminal_text(state.emulator.text_with_cursor(show=True))
                self._log_action(f"Selected terminal: {name}")
        elif t == "connect":
            # Inline connect prompt using control input
            self.connect_mode = True
            self.adding_mode = False
            self.control_input.placeholder = "Connect: <session_id>"
            self.control_input.value = ""
            self.control_input.focus()
        elif t == "action":
            aid = data.get("id")
            if aid == "mute_all":
                for name in self.terminal_manager.list_terminals():
                    state = self.terminal_manager.get_terminal_state(name)
                    if state:
                        state.item.muted = True
                self._rebuild_nav_tree()
            elif aid == "unmute_all":
                for name in self.terminal_manager.list_terminals():
                    state = self.terminal_manager.get_terminal_state(name)
                    if state:
                        state.item.muted = False
                self._rebuild_nav_tree()
            elif aid == "toggle_mirror":
                try:
                    self.chk_mirror.value = not self.chk_mirror.value
                except Exception:
                    pass
                self._rebuild_nav_tree()
            elif aid == "export_troubleshooting":
                self._export_troubleshooting_pack()
        elif t == "log":
            cat = data.get("cat", "events")
            tab_map = {
                "events": "tab-events",
                "errors": "tab-errors",
                "output": "tab-output",
                "debug": "tab-debug",
                "troubleshooting": "tab-troubleshooting",
            }
            self._switch_view(tab_map.get(cat, "tab-events"))

    # --- Scrollback navigation ----------------------------------------
    def _on_navigate(self, action: str, amount: int) -> bool:
        name = self.active_terminal
        state = self.terminal_manager.get_terminal_state(name)
        if not state:
            return False

        buf = state.scroll_buffer
        offset = self.scroll_offsets.get(name, 0)
        if action == 'wheel':
            offset = max(0, offset - amount)
        elif action == 'pageup':
            offset = max(0, offset - abs(amount))
        elif action == 'pagedown':
            offset = max(0, offset + abs(amount))
        elif action == 'home':
            offset = len(buf)
        elif action == 'end':
            offset = 0
        else:
            return False
        self.scroll_offsets[name] = offset
        state.scroll_offset = offset  # Sync to TerminalState
        self._render_scrollback(name)
        return True

    def _render_scrollback(self, name: str) -> None:
        state = self.terminal_manager.get_terminal_state(name)
        if not state:
            return

        buf = state.scroll_buffer
        offset = self.scroll_offsets.get(name, 0)
        if not buf:
            return
        # Show last screen worth with offset
        lines = buf
        height = max(10, self.size.height - 6)
        start = max(0, len(lines) - height - offset)
        view = lines[start:start+height]
        indicator = f"[SCROLLBACK offset={offset}]\n" if offset else ""
        self._set_terminal_text(indicator + "\n".join(view))


def main() -> None:
    BenchTextualApp().run()


if __name__ == "__main__":
    main()
