"""Session and participant management for AI facilitator."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class ParticipantType(Enum):
    """Type of participant in a session."""
    AI = "ai"
    HUMAN = "human"
    OBSERVER = "observer"


class ParticipantStatus(Enum):
    """Status of a participant."""
    ACTIVE = "active"
    PAUSED = "paused"
    RATE_LIMITED = "rate_limited"
    DISCONNECTED = "disconnected"


@dataclass
class Participant:
    """Represents a participant in a facilitated session."""

    id: str = field(default_factory=lambda: f"participant_{uuid4().hex[:8]}")
    name: str = "unnamed"
    type: ParticipantType = ParticipantType.AI
    provider: Optional[str] = None  # anthropic, openai, google, local
    model: Optional[str] = None     # claude-sonnet-4, gpt-4, etc.
    status: ParticipantStatus = ParticipantStatus.ACTIVE

    # Rate limiting
    messages_sent: int = 0
    last_message_at: Optional[datetime] = None
    rate_limit_reset_at: Optional[datetime] = None

    # Connection info
    websocket_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)

    def is_available(self) -> bool:
        """Check if participant can receive messages."""
        return self.status == ParticipantStatus.ACTIVE

    def mark_rate_limited(self, reset_at: datetime):
        """Mark participant as rate limited."""
        self.status = ParticipantStatus.RATE_LIMITED
        self.rate_limit_reset_at = reset_at

    def reset_rate_limit(self):
        """Clear rate limit status."""
        if self.status == ParticipantStatus.RATE_LIMITED:
            self.status = ParticipantStatus.ACTIVE
        self.rate_limit_reset_at = None


@dataclass
class Message:
    """A message in the facilitated session."""

    id: str = field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    session_id: str = ""
    from_id: str = ""
    to_id: str = ""  # or "all" for broadcast
    type: str = "chat"  # chat, system, status, control
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)

    # Delivery tracking
    delivered: bool = False
    queued: bool = False


@dataclass
class Session:
    """Represents a facilitated AI communication session."""

    id: str = field(default_factory=lambda: f"session_{uuid4().hex[:8]}")
    name: str = "Unnamed Session"
    description: str = ""

    # Participants
    participants: Dict[str, Participant] = field(default_factory=dict)

    # Messages
    messages: List[Message] = field(default_factory=list)
    message_queue: List[Message] = field(default_factory=list)

    # Session state
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    is_recording: bool = False
    is_broadcasting: bool = False

    # Broadcast viewers
    viewer_count: int = 0

    def add_participant(self, participant: Participant) -> None:
        """Add a participant to the session."""
        self.participants[participant.id] = participant

    def remove_participant(self, participant_id: str) -> None:
        """Remove a participant from the session."""
        if participant_id in self.participants:
            self.participants[participant_id].status = ParticipantStatus.DISCONNECTED

    def get_participant(self, participant_id: str) -> Optional[Participant]:
        """Get participant by ID."""
        return self.participants.get(participant_id)

    def get_active_participants(self) -> List[Participant]:
        """Get all active participants."""
        return [p for p in self.participants.values() if p.is_available()]

    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        message.session_id = self.id
        self.messages.append(message)

    def queue_message(self, message: Message) -> None:
        """Queue a message for later delivery."""
        message.queued = True
        message.session_id = self.id
        self.message_queue.append(message)

    def get_queued_messages_for(self, participant_id: str) -> List[Message]:
        """Get queued messages for a specific participant."""
        return [m for m in self.message_queue if m.to_id == participant_id]

    def start(self) -> None:
        """Start the session."""
        if not self.started_at:
            self.started_at = datetime.utcnow()

    def end(self) -> None:
        """End the session."""
        if not self.ended_at:
            self.ended_at = datetime.utcnow()
