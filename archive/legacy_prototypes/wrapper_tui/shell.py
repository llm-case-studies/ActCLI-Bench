"""Main actcli-shell TUI application."""

import asyncio
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML, ANSI
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.patch_stdout import patch_stdout

from .session_manager import SessionManager
from .terminal_tab import TerminalManager
from .wrapped_terminal import WrappedTerminal


class ShellCompleter(Completer):
    """Command completer for actcli-shell."""

    def __init__(self):
        self.commands = {
            "/add": "Add wrapped terminal (e.g., /add gemini)",
            "/viewer": "Show viewer URL",
            "/sessions": "List available sessions",
            "/connect": "Connect to session",
            "/help": "Show this help",
            "/quit": "Exit actcli-shell",
        }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lower()

        if not text.startswith("/"):
            return

        for cmd, desc in self.commands.items():
            if cmd.lower().startswith(text):
                yield Completion(
                    cmd[len(text):],
                    start_position=0,
                    display=f"{cmd} - {desc}",
                )


class Shell:
    """
    actcli-shell - Multi-terminal TUI.

    Features:
    - Tab-based terminal navigation
    - Auto-created local facilitator
    - Slash commands for control
    - Progressive complexity support
    """

    def __init__(self):
        self.session_manager = SessionManager()
        self.terminal_manager = TerminalManager()
        self.wrapped_terminals = {}  # name -> WrappedTerminal
        self.history = InMemoryHistory()
        self.completer = ShellCompleter()
        self.running = False
        self.show_tab_switch_messages = True

    def get_navbar_text(self):
        """Generate navbar with terminal tabs."""
        tabs = self.terminal_manager.tabs
        if not tabs:
            return "No terminals - Use /add to create one"

        parts = []
        for i, tab in enumerate(tabs):
            if tab.is_active:
                # Active tab - bold and highlighted
                parts.append(f"→ [{tab.name}] ←")
            else:
                parts.append(f"[{tab.name}]")

        return " ".join(parts) + " [+]"

    def get_status_text(self):
        """Generate status line."""
        session = self.session_manager.session
        if session:
            viewer_url = f"{session.facilitator_url}/viewer/{session.session_id}"
            return f"Session: {session.session_id} | Viewer: {viewer_url}"
        return "No session"

    def get_terminal_output(self):
        """Get output from active terminal."""
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            return ""

        # Read new output
        data = tab.read_output()
        if data:
            try:
                text = data.decode('utf-8', errors='replace')
                tab.output_buffer += text
            except:
                pass

        # Return last 5000 chars
        return tab.output_buffer[-5000:]

    def create_style(self):
        """Create visual style."""
        return Style.from_dict({
            "navbar": "bg:#003366 #ffffff bold",
            "status": "bg:#1e1e1e #888888",
            "prompt": "#00aaaa bold",
            "output": "#cccccc",
            "bottom-toolbar": "bg:#222222 #cccccc",
        })

    def create_key_bindings(self):
        """Create key bindings."""
        kb = KeyBindings()

        @kb.add("c-c")
        def _(event):
            """Exit on Ctrl+C."""
            self.running = False
            raise KeyboardInterrupt()

        @kb.add("c-d")
        def _(event):
            """Exit on Ctrl+D."""
            self.running = False
            raise EOFError()

        @kb.add("c-n")
        def _(event):
            """Next tab on Ctrl+N."""
            old_tab = self.terminal_manager.get_active_tab()
            self.terminal_manager.next_tab()
            new_tab = self.terminal_manager.get_active_tab()
            if old_tab != new_tab and new_tab and self.show_tab_switch_messages:
                print(f"\n➡️  Switched to tab: {new_tab.name}\n")

        @kb.add("c-p")
        def _(event):
            """Previous tab on Ctrl+P."""
            old_tab = self.terminal_manager.get_active_tab()
            self.terminal_manager.prev_tab()
            new_tab = self.terminal_manager.get_active_tab()
            if old_tab != new_tab and new_tab and self.show_tab_switch_messages:
                print(f"\n⬅️  Switched to tab: {new_tab.name}\n")

        return kb

    def get_bottom_toolbar(self):
        """Generate bottom toolbar."""
        tab = self.terminal_manager.get_active_tab()
        tab_info = f"Active: {tab.name}" if tab else "No active terminal"

        return HTML(
            f"<bottom-toolbar>{tab_info} | "
            f"Ctrl+N: Next tab | Ctrl+P: Prev tab | Ctrl+C: Exit | "
            f"Type /help for commands</bottom-toolbar>"
        )

    async def handle_command(self, command: str):
        """Handle slash commands."""
        if command.startswith("/"):
            parts = command[1:].split()
            if not parts:
                return

            cmd = parts[0].lower()

            if cmd == "add" and len(parts) > 1:
                await self.cmd_add(parts[1:])
            elif cmd == "viewer":
                await self.cmd_viewer()
            elif cmd == "sessions":
                await self.cmd_sessions()
            elif cmd == "connect" and len(parts) > 1:
                await self.cmd_connect(parts[1])
            elif cmd == "help":
                await self.cmd_help()
            elif cmd == "quit":
                self.running = False
                return "quit"
            else:
                print(f"Unknown command: {cmd}")
        else:
            # Regular input - send to active terminal
            tab = self.terminal_manager.get_active_tab()
            if tab:
                tab.write_input((command + "\n").encode())
            else:
                print("No active terminal. Use /add to create one.")

    async def cmd_add(self, args):
        """Add a new wrapped terminal: /add <command>"""
        command = args
        name = command[0] if command else "terminal"

        # Add tab to manager
        tab = self.terminal_manager.add_tab(name, command)

        # Create wrapped terminal connected to facilitator
        if self.session_manager.session:
            wrapped = WrappedTerminal(
                name=name,
                command=command,
                session_id=self.session_manager.session.session_id,
                facilitator_url=self.session_manager.facilitator_url,
            )

            print(f"\n⏳ Starting {name} and connecting to facilitator...")
            success = await wrapped.start()

            if success:
                self.wrapped_terminals[name] = wrapped
                print(f"✅ Connected: {name}")
                print(f"📋 Now active. Type to interact, or /add to add more terminals.\n")
            else:
                # Remove tab if connection failed
                self.terminal_manager.close_tab(len(self.terminal_manager.tabs) - 1)
                print(f"❌ Failed to connect {name}\n")
        else:
            print(f"❌ No active session\n")

    async def cmd_viewer(self):
        """Show viewer URL: /viewer"""
        session = self.session_manager.session
        if session:
            viewer_url = f"{session.facilitator_url}/viewer/{session.session_id}"
            print(f"\n🔗 Live Viewer URL:")
            print(f"   {viewer_url}")
            print(f"\n💡 Open this URL in your browser to watch the conversation live!\n")
        else:
            print("\n❌ No active session\n")

    async def cmd_sessions(self):
        """List available sessions: /sessions"""
        sessions = await self.session_manager.list_sessions()
        if sessions:
            print("\nAvailable sessions:")
            for s in sessions:
                print(f"  {s['id']} - {s['name']} ({s['participant_count']} participants)")
        else:
            print("\nNo sessions available")
        print()

    async def cmd_connect(self, session_id: str):
        """Connect to session: /connect <session_id>"""
        success = await self.session_manager.join_session(session_id, "shell")
        if success:
            print(f"\n✅ Connected to session: {session_id}\n")
        else:
            print(f"\n❌ Failed to connect to session: {session_id}\n")

    async def cmd_help(self):
        """Show help."""
        help_text = """
╔════════════════════════════════════════════════════════════╗
║                 actcli-shell Quick Help                    ║
╚════════════════════════════════════════════════════════════╝

SLASH COMMANDS:
  /add <command>        Add wrapped terminal (e.g., /add gemini)
  /viewer               Show live viewer URL
  /sessions             List available sessions
  /connect <id>         Connect to session
  /help                 Show this help
  /quit                 Exit

KEYBINDINGS:
  Ctrl+N                Next tab
  Ctrl+P                Previous tab
  Ctrl+C                Exit

USAGE:
  1. Add terminals with /add (e.g., /add gemini, /add tree)
  2. Navigate between tabs with Ctrl+N/P
  3. Type directly to interact with active terminal
  4. Use slash commands for control

TERMINAL OUTPUT:
  Terminal output appears above as you interact with the active
  terminal. The navbar shows all open terminals.

TIPS:
  • Start simple: /add cat or /add bc
  • Try AI: /add gemini or /add codex
  • Docker: /add docker exec -it container bash
  • Remote: /add ssh user@host "gemini"

Press Enter to continue...
"""
        print(help_text)

    async def print_status(self):
        """Print current status."""
        print("\n" + "=" * 60)
        print(f"📊 STATUS: {self.get_status_text()}")
        print(f"📑 NAVBAR: {self.get_navbar_text()}")
        print("=" * 60)

        # Print terminal output if available
        tab = self.terminal_manager.get_active_tab()
        if tab:
            output = self.get_terminal_output()
            if output:
                print("\n" + "─" * 60)
                print(f"OUTPUT FROM: {tab.name}")
                print("─" * 60)
                # Print with ANSI codes
                print(output)
                print("─" * 60)

    async def initialize(self):
        """Initialize session and facilitator."""
        print("\n" + "=" * 60)
        print("🚀 Starting actcli-shell...")
        print("=" * 60)

        print("\n📡 Starting local facilitator...")
        success = await self.session_manager.start_local_facilitator()

        if success:
            print("✅ Facilitator started")
            print("\n🎯 Creating default session...")

            success = await self.session_manager.create_default_session()
            if success:
                session_id = self.session_manager.session.session_id
                viewer_url = f"{self.session_manager.facilitator_url}/viewer/{session_id}"

                print(f"✅ Session created: {session_id}")
                print(f"\n🔗 Live Viewer: {viewer_url}")
                print("\n" + "=" * 60)
                print("Type /help for commands")
                print("Type /add <command> to start a terminal (e.g., /add gemini)")
                print("Type /viewer to see the viewer URL again")
                print("=" * 60 + "\n")
            else:
                print("❌ Failed to create session")
        else:
            print("❌ Failed to start facilitator")

    async def run_async(self):
        """Async run loop."""
        # Initialize
        await self.initialize()

        # Create session with bindings and style
        session = PromptSession(
            history=self.history,
            completer=self.completer,
            key_bindings=self.create_key_bindings(),
            style=self.create_style(),
            bottom_toolbar=self.get_bottom_toolbar,
            complete_while_typing=False,
            mouse_support=False,  # Disable to prevent mouse events from leaking to other AIs
        )

        self.running = True

        # Main input loop
        with patch_stdout():
            while self.running:
                try:
                    # Print status before each prompt
                    await self.print_status()

                    # Get input
                    text = await session.prompt_async(
                        HTML("\n<prompt>actcli-shell></prompt> "),
                        refresh_interval=0.1,  # Refresh for terminal output updates
                    )

                    # Handle None from Ctrl+D/Ctrl+C
                    if text is None:
                        break

                    text = text.strip()
                    if text:
                        result = await self.handle_command(text)
                        if result == "quit":
                            break

                    # Small delay to let terminal output accumulate
                    await asyncio.sleep(0.1)

                except (EOFError, KeyboardInterrupt):
                    break

        self.cleanup()

    async def cleanup_async(self):
        """Async cleanup of wrapped terminals."""
        # Stop all wrapped terminals
        for wrapped in self.wrapped_terminals.values():
            try:
                await wrapped.stop()
            except Exception as e:
                print(f"Warning: Error stopping {wrapped.name}: {e}")

    def cleanup(self):
        """Cleanup resources."""
        print("\n\n🧹 Cleaning up...")

        # Stop wrapped terminals using current event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule cleanup as task
                for wrapped in self.wrapped_terminals.values():
                    try:
                        asyncio.create_task(wrapped.stop())
                    except:
                        pass
            else:
                # Run cleanup synchronously
                asyncio.run(self.cleanup_async())
        except:
            pass

        self.terminal_manager.close_all()
        self.session_manager.cleanup()
        print("👋 Goodbye!\n")

    def run(self):
        """Run the shell."""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            pass


def main():
    """
    Entry point for actcli-shell command.

    actcli-shell - Multi-terminal TUI for AI collaboration.

    Features:
    - Tab-based terminal navigation
    - Auto-created local facilitator
    - Slash commands for control
    - Real-time multi-AI conversations

    Usage:
        actcli-shell              # Launch the TUI

    Slash commands (inside TUI):
        /add <name> <cmd>        # Add new terminal
        /switch <tab>            # Switch to terminal tab
        /close                   # Close current terminal
        /quit                    # Exit application
    """
    import sys

    # Handle --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print(main.__doc__)
        return

    # Check if running in a TTY
    if not sys.stdin.isatty():
        print("Error: actcli-shell requires a TTY terminal to run.", file=sys.stderr)
        print("Please run this command in a real terminal, not in a pipe or redirect.", file=sys.stderr)
        sys.exit(1)

    shell = Shell()
    shell.run()


if __name__ == "__main__":
    main()
