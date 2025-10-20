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
    ListView,
    ListItem,
    Log,
    Checkbox,
    Label,
    Tree,
)

from dataclasses import dataclass
from typing import Dict, Optional, List
import shlex
import re

from ..wrapper_tui.session_manager import SessionManager
from ..wrapper.client import FacilitatorClient
from .terminal_runner import TerminalRunner
from .term_emulator import EmulatedTerminal
from .term_view import TermView


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

    async def on_mount(self) -> None:
        # Start with the first palette
        self.add_class("theme-ledger")
        # App state
        self.session_manager = SessionManager()
        self.viewer_url: Optional[str] = None
        self.facilitator_client: Optional[FacilitatorClient] = None
        self.terminals: Dict[str, TerminalItem] = {}
        self.active_terminal: Optional[str] = None
        self.mirror_to_facilitator: bool = False
        self.last_broadcast: Optional[str] = None
        self.adding_mode: bool = False
        self.connect_mode: bool = False
        self._nav_items: Dict[int, str] = {}
        self.action_lines: List[str] = []
        # Kick off session bootstrap
        await self._bootstrap_session_async()
        self.emulators: Dict[str, EmulatedTerminal] = {}
        # Scrollback state
        self.scroll_buffers: Dict[str, list[str]] = {}
        self.scroll_offsets: Dict[str, int] = {}
        self.max_scrollback_lines: int = 2000
        # Build nav tree after state is ready
        try:
            self._rebuild_nav_tree()
        except Exception:
            pass
        # Log module path to help verify running code
        try:
            self._log_action(f"Bench module: {__file__}")
        except Exception:
            pass

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
                self.terminal_view = TermView(id="terminal-view")
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

    def _set_terminal_text(self, text: str) -> None:
        view = getattr(self, "terminal_view", None)
        if view:
            try:
                view.update(text)
            except Exception:
                pass

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

    def _append_terminal_output(self, name: str, text: str) -> None:
        """Feed emulator for terminal 'name' and refresh view if active."""
        emu = self.emulators.get(name)
        if not emu:
            emu = EmulatedTerminal()
            self.emulators[name] = emu
        emu.feed(text)
        # Append to scrollback buffer (plain lines)
        sb = self.scroll_buffers.setdefault(name, [])
        for line in text.splitlines():
            clean = self._strip_ansi(line)
            if clean:
                sb.append(clean)
                if len(sb) > self.max_scrollback_lines:
                    del sb[: len(sb) - self.max_scrollback_lines]
        if self.active_terminal == name and self.active_view == "terminal" and self.scroll_offsets.get(name, 0) == 0:
            # Show cursor when in terminal view and not scrolled away
            self._set_terminal_text(emu.text_with_cursor(show=self.terminal_view.focused))

    # ANSI/control filtering adapted from wrapper.pty_wrapper
    def _strip_ansi(self, s: str) -> str:
        patterns = [
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])",
            r"\x1B\][^\x07]*\x07",
            r"\x1B\][^\x1B]*\x1B\\",
            r"\x1B[PX^_][^\x1B]*\x1B\\",
            r"\x1B[\[\]()][0-9;]*[A-Za-z<>]",
        ]
        out = s
        for p in patterns:
            out = re.sub(p, "", out)
        return out

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
        if ok and self.session_manager.session:
            sid = self.session_manager.session.session_id
            self.viewer_url = f"{self.session_manager.facilitator_url}/viewer/{sid}"
            self._set_title_status(sid)
            # Connect as moderator (optional mirror)
            self.facilitator_client = FacilitatorClient(self.session_manager.facilitator_url)
            try:
                await self.facilitator_client.join_session(sid, "moderator", participant_type="human")
                await self.facilitator_client.connect_websocket()
            except Exception:
                self.facilitator_client = None
                self._log_action("Moderator WS connect failed (mirror disabled)")

    def _set_title_status(self, session_id: str) -> None:
        if getattr(self, "status_line", None):
            self.status_line.update(f"Terminal  |  Session: {session_id}  |  Viewer: {self.viewer_url}")

    def _handle_broadcast(self, text: str) -> None:
        """Broadcast a line to all unmuted terminals; optionally mirror to viewer."""
        self.last_broadcast = text
        # Inject into each unmuted terminal
        for item in self.terminals.values():
            if not item.muted:
                item.runner.inject(text)
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
        if bid == "btn-add":
            # Toggle add mode: next Enter/Broadcast parses as add spec
            self.adding_mode = True
            self.connect_mode = False
            self.control_input.placeholder = "Add terminal: <name> <command...>  (e.g., CO codex)"
            self.control_input.value = ""
            self.control_input.focus()
        elif bid == "btn-connect":
            # Toggle connect mode: join existing session
            self.connect_mode = True
            self.adding_mode = False
            self.control_input.placeholder = "Connect: <session_id>"
            self.control_input.value = ""
            self.control_input.focus()
        elif bid == "btn-mute-all":
            for item in self.terminals.values():
                item.muted = True
            self._refresh_nav()
        elif bid == "btn-unmute-all":
            for item in self.terminals.values():
                item.muted = False
            self._refresh_nav()
        elif bid == "btn-broadcast":
            text = self.control_input.value.strip()
            if text:
                if self.adding_mode:
                    self._handle_add_from_text(text)
                elif self.connect_mode:
                    self._handle_connect_from_text(text)
                else:
                    self._handle_broadcast(text)
                self.control_input.value = ""
        elif bid in ("tab-terminal", "tab-events", "tab-errors", "tab-output", "tab-debug"):
            self._switch_view(bid)

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[attr-defined]
        # Activate selected terminal by index mapping first
        idx = getattr(event, "index", None)
        name: Optional[str] = None
        if isinstance(idx, int):
            name = self._nav_items.get(idx)
        if not name:
            # Fallback to label parsing
            try:
                label = event.item.renderable  # Static or Label
                name = str(getattr(label, "text", getattr(label, "renderable", label)))
            except Exception:
                name = str(event.item)
            name = name.split(" ", 1)[0] if name else None
        if name == "__logs__":
            self.active_terminal = "__logs__"
            self._set_terminal_text("\n".join(self.action_lines[-500:]) or "(no logs)" )
            self._log_action("Opened Logs view")
        elif name and name in self.terminals:
            self.active_terminal = name
            emu = self.emulators.get(name) or EmulatedTerminal()
            self.emulators[name] = emu
            self._set_terminal_text(f"→ Active: {name}\n" + emu.text_with_cursor())
            # Focus terminal view and wire writer to active runner
            self.terminal_view.set_writer(self._write_to_active)
            self.terminal_view.set_navigator(self._on_navigate)
            self.terminal_view.focus()
            self._log_action(f"Selected terminal: {name}")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:  # type: ignore[attr-defined]
        # Also switch on highlight change for mouse/keyboard navigation
        try:
            label = event.item.renderable
            name = str(getattr(label, "text", getattr(label, "renderable", label)))
        except Exception:
            name = str(event.item)
        name = name.split(" ", 1)[0]
        if name == "__logs__" and name != self.active_terminal:
            self.active_terminal = "__logs__"
            self._set_terminal_text("\n".join(self.action_lines[-500:]) or "(no logs)")
            self._log_action("Highlighted Logs view")
        elif name in self.terminals and name != self.active_terminal:
            self.active_terminal = name
            emu = self.emulators.get(name) or EmulatedTerminal()
            self.emulators[name] = emu
            self._set_terminal_text(f"→ Active: {name}\n" + emu.text_with_cursor())
            self.terminal_view.set_writer(self._write_to_active)
            self._log_action(f"Highlighted terminal: {name}")

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
        if name in self.terminals:
            self._log(f"Terminal '{name}' already exists")
            return
        runner = TerminalRunner(name=name, command=cmd, muted=True)
        runner.on_output(lambda text, n=name: self.call_from_thread(self._append_terminal_output, n, text))
        ok = runner.start()
        if not ok:
            self._log(f"Failed to start: {' '.join(cmd)}")
            self._log_action(f"Start failed for {name}: {' '.join(cmd)}")
            return
        self.terminals[name] = TerminalItem(name=name, command=cmd, runner=runner, muted=True)
        # init emulator buffer
        self.emulators[name] = EmulatedTerminal()
        if not self.active_terminal:
            self.active_terminal = name
        self._refresh_nav()
        self._set_terminal_text(f"Added terminal '{name}' → {' '.join(cmd)}  [muted]")
        self._log_action(f"Added: {name} cmd={' '.join(cmd)} [muted]")
        # Prepare scrollback structures
        self.scroll_buffers[name] = []
        self.scroll_offsets[name] = 0

    # --- View switching -------------------------------------------------
    def _switch_view(self, tab_id: str) -> None:
        if tab_id == "tab-terminal":
            self.active_view = "terminal"
            name = self.active_terminal
            text = ""
            if name and name in self.emulators:
                text = self.emulators[name].text_with_cursor()
            self._set_terminal_text(text)
            self.terminal_view.set_writer(self._write_to_active)
            self.terminal_view.focus()
            return

        # Logs view
        self.terminal_view.set_writer(None)
        mapping = {
            "tab-events": "events",
            "tab-errors": "errors",
            "tab-output": "output",
            "tab-debug": "debug",
        }
        cat = mapping.get(tab_id, "events")
        self.active_view = f"log:{cat}"
        self._set_terminal_text(self.log_manager.text(cat) or f"(no {cat})")

    # Write bytes/strings to the active terminal's PTY
    def _write_to_active(self, data: str) -> None:
        name = self.active_terminal
        if not name or name == "__logs__":
            return
        item = self.terminals.get(name)
        if not item:
            return
        try:
            item.runner.write(data)
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
        for name, item in self.terminals.items():
            mark = "[M]" if item.muted else "[U]"
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
        logs_node = self.nav_tree.root.add("Logs")
        for cat in ("Events", "Errors", "Output", "Debug"):
            n = logs_node.add(cat)
            n.data = {"type": "log", "cat": cat.lower()}
        self.nav_tree.root.expand()
        terminals_node.expand()
        sessions_node.expand()
        settings_node.expand()
        logs_node.expand()

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
            if name in self.terminals:
                self.active_terminal = name
                emu = self.emulators.get(name) or EmulatedTerminal()
                self.emulators[name] = emu
                self.active_view = "terminal"
                self._set_terminal_text(emu.text_with_cursor(show=True))
                self.terminal_view.set_writer(self._write_to_active)
                self.terminal_view.set_navigator(self._on_navigate)
                self.terminal_view.focus()
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
                for item in self.terminals.values():
                    item.muted = True
                self._rebuild_nav_tree()
            elif aid == "unmute_all":
                for item in self.terminals.values():
                    item.muted = False
                self._rebuild_nav_tree()
            elif aid == "toggle_mirror":
                try:
                    self.chk_mirror.value = not self.chk_mirror.value
                except Exception:
                    pass
                self._rebuild_nav_tree()
        elif t == "log":
            cat = data.get("cat", "events")
            self._switch_view({
                "events": "tab-events",
                "errors": "tab-errors",
                "output": "tab-output",
                "debug": "tab-debug",
            }[cat])

    # --- Scrollback navigation ----------------------------------------
    def _on_navigate(self, action: str, amount: int) -> bool:
        name = self.active_terminal
        if not name or name not in self.scroll_buffers:
            return False
        # Ensure buffer exists
        buf = self.scroll_buffers[name]
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
        self._render_scrollback(name)
        return True

    def _render_scrollback(self, name: str) -> None:
        buf = self.scroll_buffers.get(name, [])
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
