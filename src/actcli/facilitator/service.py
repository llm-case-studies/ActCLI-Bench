"""Facilitator service - FastAPI server for AI communication."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .session import Session, Participant, Message, ParticipantType, ParticipantStatus


# Pydantic models for API
class CreateSessionRequest(BaseModel):
    name: str
    description: str = ""


class JoinSessionRequest(BaseModel):
    session_id: str
    name: str
    type: str = "ai"
    provider: Optional[str] = None
    model: Optional[str] = None


class SendMessageRequest(BaseModel):
    session_id: str
    from_id: str
    to_id: str  # or "all"
    content: str
    type: str = "chat"
    metadata: Dict = {}


class FacilitatorService:
    """Smart facilitator service for multi-AI communication."""

    def __init__(self):
        self.app = FastAPI(
            title="AI Facilitator Service",
            description="WebSocket-based message routing for multi-AI communication",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )
        self.sessions: Dict[str, Session] = {}
        self.websockets: Dict[str, WebSocket] = {}  # participant_id -> websocket

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register FastAPI routes."""

        @self.app.post("/sessions")
        async def create_session(req: CreateSessionRequest):
            """Create a new session."""
            session = Session(name=req.name, description=req.description)
            self.sessions[session.id] = session
            return {
                "session_id": session.id,
                "name": session.name,
                "created_at": session.created_at.isoformat(),
            }

        @self.app.get("/sessions")
        async def list_sessions():
            """List all sessions."""
            return {
                "sessions": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "participant_count": len(s.participants),
                        "message_count": len(s.messages),
                        "is_broadcasting": s.is_broadcasting,
                        "viewer_count": s.viewer_count,
                    }
                    for s in self.sessions.values()
                ]
            }

        @self.app.get("/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get session details."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            return {
                "id": session.id,
                "name": session.name,
                "description": session.description,
                "participants": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "type": p.type.value,
                        "status": p.status.value,
                        "provider": p.provider,
                        "model": p.model,
                    }
                    for p in session.participants.values()
                ],
                "message_count": len(session.messages),
                "is_broadcasting": session.is_broadcasting,
            }

        @self.app.get("/sessions/{session_id}/messages")
        async def get_session_messages(
            session_id: str,
            limit: int = 50,
            offset: int = 0
        ):
            """Get messages from a session."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            messages = session.messages[offset:offset + limit]
            return {
                "session_id": session_id,
                "total": len(session.messages),
                "offset": offset,
                "limit": limit,
                "messages": [self._message_to_dict(msg) for msg in messages]
            }

        @self.app.post("/sessions/{session_id}/join")
        async def join_session(session_id: str, req: JoinSessionRequest):
            """Join a session as a participant."""
            session = self.sessions.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            participant = Participant(
                name=req.name,
                type=ParticipantType(req.type),
                provider=req.provider,
                model=req.model,
            )
            session.add_participant(participant)

            return {
                "participant_id": participant.id,
                "session_id": session.id,
            }

        @self.app.post("/messages")
        async def send_message(req: SendMessageRequest):
            """Send a message in a session."""
            session = self.sessions.get(req.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            message = Message(
                session_id=req.session_id,
                from_id=req.from_id,
                to_id=req.to_id,
                type=req.type,
                content=req.content,
                metadata=req.metadata,
            )

            # Check if sender is rate limited
            sender = session.get_participant(req.from_id)
            if sender and sender.status == ParticipantStatus.RATE_LIMITED:
                session.queue_message(message)
                return {
                    "message_id": message.id,
                    "status": "queued",
                    "reason": "rate_limited",
                }

            # Route the message
            await self._route_message(session, message)

            return {
                "message_id": message.id,
                "status": "delivered",
            }

        @self.app.websocket("/ws/{session_id}/{participant_id}")
        async def websocket_endpoint(
            websocket: WebSocket,
            session_id: str,
            participant_id: str,
        ):
            """WebSocket endpoint for real-time communication."""
            await websocket.accept()

            session = self.sessions.get(session_id)
            if not session:
                await websocket.close(code=1008, reason="Session not found")
                return

            participant = session.get_participant(participant_id)
            if not participant:
                await websocket.close(code=1008, reason="Participant not found")
                return

            # Register websocket
            self.websockets[participant_id] = websocket
            participant.websocket_id = participant_id

            try:
                # Send queued messages
                queued = session.get_queued_messages_for(participant_id)
                for msg in queued:
                    await websocket.send_json(self._message_to_dict(msg))
                    session.message_queue.remove(msg)

                # Listen for messages
                while True:
                    data = await websocket.receive_json()
                    await self._handle_websocket_message(
                        session, participant, data
                    )

            except WebSocketDisconnect:
                del self.websockets[participant_id]
                participant.status = ParticipantStatus.DISCONNECTED

        @self.app.get("/viewer/{session_id}")
        async def viewer_page(session_id: str):
            """HTML viewer page for watching a session."""
            from fastapi.responses import HTMLResponse

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Session Viewer - {session_id}</title>
                <style>
                    body {{
                        font-family: monospace;
                        background: #1e1e1e;
                        color: #d4d4d4;
                        padding: 20px;
                        margin: 0;
                    }}
                    h1 {{ color: #4ec9b0; }}
                    #messages {{
                        border: 1px solid #3e3e3e;
                        padding: 15px;
                        height: 500px;
                        overflow-y: auto;
                        background: #252526;
                        border-radius: 5px;
                    }}
                    .message {{
                        margin: 10px 0;
                        padding: 8px;
                        background: #2d2d30;
                        border-left: 3px solid #007acc;
                        border-radius: 3px;
                    }}
                    .from {{ color: #4ec9b0; font-weight: bold; }}
                    .time {{ color: #808080; font-size: 0.9em; }}
                    .content {{ margin-top: 5px; }}
                    #status {{
                        color: #ce9178;
                        margin: 10px 0;
                        padding: 10px;
                        background: #2d2d30;
                        border-radius: 3px;
                    }}
                </style>
            </head>
            <body>
                <h1>🎬 AI Reality Show - Session Viewer</h1>
                <div id="status">Connecting to session {session_id}...</div>
                <div id="messages"></div>

                <script>
                    const sessionId = "{session_id}";
                    const ws = new WebSocket(`ws://${{window.location.host}}/broadcast/${{sessionId}}`);
                    const messagesDiv = document.getElementById('messages');
                    const statusDiv = document.getElementById('status');

                    ws.onopen = () => {{
                        statusDiv.textContent = '✅ Connected - Watching live messages...';
                        statusDiv.style.color = '#4ec9b0';
                    }};

                    ws.onmessage = (event) => {{
                        const msg = JSON.parse(event.data);
                        const msgDiv = document.createElement('div');
                        msgDiv.className = 'message';

                        const timestamp = new Date(msg.timestamp).toLocaleTimeString();
                        msgDiv.innerHTML = `
                            <span class="from">${{msg.from_name}}</span>
                            <span class="time">at ${{timestamp}}</span>
                            <div class="content">${{msg.content}}</div>
                        `;

                        messagesDiv.appendChild(msgDiv);
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    }};

                    ws.onerror = () => {{
                        statusDiv.textContent = '❌ Connection error';
                        statusDiv.style.color = '#f48771';
                    }};

                    ws.onclose = () => {{
                        statusDiv.textContent = '⚠️ Connection closed';
                        statusDiv.style.color = '#ce9178';
                    }};
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        @self.app.websocket("/broadcast/{session_id}")
        async def broadcast_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket endpoint for viewers (broadcast mode)."""
            await websocket.accept()

            session = self.sessions.get(session_id)
            if not session:
                await websocket.close(code=1008, reason="Session not found")
                return

            session.viewer_count += 1
            session.is_broadcasting = True

            try:
                # Send session history
                for msg in session.messages[-50:]:  # Last 50 messages
                    await websocket.send_json(self._message_to_dict(msg))

                # Store this viewer's websocket
                viewer_id = f"viewer_{id(websocket)}"
                self.websockets[viewer_id] = websocket

                # Keep connection alive - new messages will be pushed
                while True:
                    await asyncio.sleep(1)

            except WebSocketDisconnect:
                session.viewer_count -= 1
                if viewer_id in self.websockets:
                    del self.websockets[viewer_id]
                if session.viewer_count == 0:
                    session.is_broadcasting = False

    async def _route_message(self, session: Session, message: Message):
        """Route a message to appropriate recipient(s)."""
        session.add_message(message)

        # Broadcast to all if target is "all"
        if message.to_id == "all":
            for p in session.get_active_participants():
                if p.id != message.from_id:  # Don't echo back
                    await self._deliver_to_participant(p, message)
        else:
            # Send to specific participant
            recipient = session.get_participant(message.to_id)
            if recipient and recipient.is_available():
                await self._deliver_to_participant(recipient, message)
            elif recipient:
                # Queue if recipient not available
                session.queue_message(message)

        # Broadcast to viewers if session is broadcasting
        if session.is_broadcasting:
            await self._broadcast_to_viewers(session, message)

    async def _deliver_to_participant(
        self, participant: Participant, message: Message
    ):
        """Deliver a message to a participant via WebSocket."""
        if participant.websocket_id in self.websockets:
            ws = self.websockets[participant.websocket_id]
            try:
                msg_dict = self._message_to_dict(message)
                await ws.send_json(msg_dict)
                message.delivered = True
            except Exception:
                # WebSocket closed, queue the message
                message.queued = True

    async def _broadcast_to_viewers(self, session: Session, message: Message):
        """Broadcast a message to all viewers."""
        msg_dict = self._message_to_dict(message)
        # Send to all viewer websockets
        for ws_id, ws in list(self.websockets.items()):
            if ws_id.startswith("viewer_"):
                try:
                    await ws.send_json(msg_dict)
                except Exception:
                    # Viewer disconnected
                    pass

    async def _handle_websocket_message(
        self, session: Session, participant: Participant, data: dict
    ):
        """Handle incoming WebSocket message."""
        msg_type = data.get("type", "chat")

        if msg_type == "chat":
            message = Message(
                session_id=session.id,
                from_id=participant.id,
                to_id=data.get("to", "all"),
                content=data.get("content", ""),
                metadata=data.get("metadata", {}),
            )
            await self._route_message(session, message)

        elif msg_type == "status":
            # Update participant status
            new_status = data.get("status")
            if new_status:
                participant.status = ParticipantStatus(new_status)

    def _message_to_dict(self, message: Message) -> dict:
        """Convert message to dict for JSON serialization."""
        # Get sender name from session
        session = self.sessions.get(message.session_id)
        sender = session.get_participant(message.from_id) if session else None
        from_name = sender.name if sender else "Unknown"

        return {
            "id": message.id,
            "session_id": message.session_id,
            "from": message.from_id,
            "from_name": from_name,
            "to": message.to_id,
            "type": message.type,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
        }


def create_app() -> FastAPI:
    """Create and return the FastAPI app."""
    service = FacilitatorService()
    return service.app
