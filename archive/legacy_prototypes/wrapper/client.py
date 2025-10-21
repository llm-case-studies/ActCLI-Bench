"""Facilitator client for terminal wrappers."""

import asyncio
import json
from typing import Callable, Optional
import httpx
import websockets


class FacilitatorClient:
    """Client for connecting to the facilitator service."""

    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.session_id: Optional[str] = None
        self.participant_id: Optional[str] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._message_callback: Optional[Callable] = None

    async def create_session(self, name: str, description: str = "") -> str:
        """Create a new session."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sessions",
                json={"name": name, "description": description},
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = data["session_id"]
            return self.session_id

    async def join_session(
        self,
        session_id: str,
        name: str,
        participant_type: str = "ai",
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Join an existing session."""
        self.session_id = session_id
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sessions/{session_id}/join",
                json={
                    "session_id": session_id,
                    "name": name,
                    "type": participant_type,
                    "provider": provider,
                    "model": model,
                },
            )
            response.raise_for_status()
            data = response.json()
            self.participant_id = data["participant_id"]
            return self.participant_id

    async def connect_websocket(self):
        """Connect to facilitator via WebSocket."""
        if not self.session_id or not self.participant_id:
            raise ValueError("Must join session before connecting WebSocket")

        ws_endpoint = f"{self.ws_url}/ws/{self.session_id}/{self.participant_id}"
        self.websocket = await websockets.connect(ws_endpoint)

    async def send_message(
        self,
        content: str,
        to: str = "all",
        msg_type: str = "chat",
        metadata: dict = None,
    ):
        """Send a message via WebSocket."""
        if not self.websocket:
            raise ValueError("WebSocket not connected")

        message = {
            "type": msg_type,
            "to": to,
            "content": content,
            "metadata": metadata or {},
        }
        await self.websocket.send(json.dumps(message))

    async def send_raw(self, payload: dict):
        """Send a raw JSON payload over WebSocket.

        Useful for non-chat control messages (e.g., status updates).
        """
        if not self.websocket:
            raise ValueError("WebSocket not connected")
        await self.websocket.send(json.dumps(payload))

    async def send_status(self, status: str):
        """Send a participant status update (active|paused|rate_limited)."""
        await self.send_raw({
            "type": "status",
            "status": status,
        })

    async def listen(self, callback: Callable):
        """Listen for messages from facilitator."""
        if not self.websocket:
            raise ValueError("WebSocket not connected")

        self._message_callback = callback

        async for message in self.websocket:
            data = json.loads(message)
            if self._message_callback:
                await self._message_callback(data)

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
