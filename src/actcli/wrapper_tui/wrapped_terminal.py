"""Wrapped terminal that connects to facilitator.

Note: This is a simplified version for actcli-shell that doesn't try to
control stdin (which conflicts with the shell's prompt). Instead, it just
connects to the facilitator and listens for messages.
"""

import asyncio
from typing import List, Optional

from ..wrapper.client import FacilitatorClient


class WrappedTerminal:
    """A terminal that's wrapped and connected to facilitator."""

    def __init__(
        self,
        name: str,
        command: List[str],
        session_id: str,
        facilitator_url: str = "http://localhost:8765",
    ):
        self.name = name
        self.command = command
        self.session_id = session_id
        self.facilitator_url = facilitator_url
        self.client: Optional[FacilitatorClient] = None
        self.listen_task: Optional[asyncio.Task] = None
        self.participant_id: Optional[str] = None

    async def start(self):
        """Start the wrapped terminal and connect to facilitator."""
        try:
            # Create client
            self.client = FacilitatorClient(self.facilitator_url)

            # Join session
            self.participant_id = await self.client.join_session(
                session_id=self.session_id,
                name=self.name,
                provider="cli",  # Generic CLI provider
                model=self.name,  # Use name as model identifier
            )

            # Connect WebSocket
            await self.client.connect_websocket()

            # Start listening for messages from facilitator
            async def on_message(data: dict):
                """Handle messages from facilitator."""
                if data.get("type") == "chat":
                    content = data.get("content", "")
                    from_participant = data.get("from", "")

                    # Don't echo our own messages
                    if from_participant == self.participant_id:
                        return

                    from_name = data.get("from_name", "Unknown")
                    # For now, just print messages (later we can inject into terminal)
                    print(f"\n[{from_name} → {self.name}]: {content}")

            self.listen_task = asyncio.create_task(
                self.client.listen(on_message)
            )

            return True

        except Exception as e:
            print(f"❌ Failed to start {self.name}: {e}")
            return False

    async def send_message(self, content: str):
        """Send a message to the facilitator."""
        if self.client:
            await self.client.send_message(
                content=content,
                to="all",
                msg_type="chat"
            )

    async def stop(self):
        """Stop the wrapped terminal."""
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        if self.client:
            await self.client.close()

    def is_running(self) -> bool:
        """Check if terminal is still running."""
        return self.listen_task is not None and not self.listen_task.done()
