"""Mock backend API for the ActCLI Round Table frontend prototype.

Run locally with:

    uvicorn main:app --reload

The mock data lives in-memory; restarting the server resets everything.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Literal, Optional

from dateutil import tz
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="ActCLI Round Table Mock API", root_path="/api")

UTC = tz.UTC


class TopicStatus(str, Literal["pending", "approved", "scheduled"]):
    pass


class Topic(BaseModel):
    id: str
    title: str
    description: str
    context_link: Optional[str] = None
    status: TopicStatus = "pending"
    votes: int = 0
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    submitter: Optional[str] = None


class TopicCreate(BaseModel):
    title: str = Field(..., max_length=120)
    description: str = Field(..., max_length=1000)
    context_link: Optional[str] = None
    submitter: Optional[str] = None


class VoteRequest(BaseModel):
    delta: int = Field(1, description="Vote change, 1 for upvote, -1 for downvote")


class Participant(BaseModel):
    role: str
    model: str


class SessionState(str, Literal["upcoming", "active", "completed"]):
    pass


class Session(BaseModel):
    id: str
    topic_id: str
    title: str
    scheduled_for: datetime
    state: SessionState
    format: str
    participants: List[Participant]
    summary: Optional[str] = None
    artifacts: Optional[dict] = None


class SessionCreate(BaseModel):
    topic_id: str
    format_id: str
    scheduled_for: datetime


# --- In-memory store -------------------------------------------------------

topics: List[Topic] = [
    Topic(
        id="topic_001",
        title="AI and climate adaptation",
        description="Discuss near-term vs long-term interventions and ethical risks.",
        context_link="https://example.com/article",
        status="approved",
        votes=42,
        submitted_at=datetime.now(tz=UTC) - timedelta(hours=6),
    ),
    Topic(
        id="topic_002",
        title="Should open-weight models be regulated?",
        description="Debate pros/cons of licensing requirements for OSS models.",
        status="pending",
        votes=17,
        submitted_at=datetime.now(tz=UTC) - timedelta(hours=2),
    ),
]

sessions: List[Session] = [
    Session(
        id="session_101",
        topic_id="topic_001",
        title="AI and climate adaptation",
        scheduled_for=datetime.now(tz=UTC) + timedelta(hours=4),
        state="upcoming",
        format="consensus-round-table",
        participants=[
            Participant(role="Facilitator", model="claude-3-5-sonnet"),
            Participant(role="Expert-A", model="gpt-4o"),
            Participant(role="Expert-B", model="gemini-1.5-flash"),
        ],
    ),
    Session(
        id="session_102",
        topic_id="topic_999",
        title="Synthetic Biology Ethics",
        scheduled_for=datetime.now(tz=UTC) - timedelta(days=1),
        state="completed",
        format="debate-pro-con",
        participants=[
            Participant(role="Facilitator", model="claude-3-opus"),
            Participant(role="Advocate", model="gpt-4o"),
            Participant(role="Skeptic", model="gemini-1.5-pro"),
        ],
        summary="Panel agreed on need for transparent oversight and tiered licensing.",
        artifacts={
            "pdf": "https://cdn.example.com/archive/session_102.pdf",
            "transcript": "https://cdn.example.com/archive/session_102.json",
        },
    ),
]

# simulate an active session for the live viewer
sessions.append(
    Session(
        id="session_live",
        topic_id="topic_live",
        title="AI for disaster response",
        scheduled_for=datetime.now(tz=UTC) - timedelta(minutes=5),
        state="active",
        format="lightning-round",
        participants=[
            Participant(role="Facilitator", model="claude-3-haiku"),
            Participant(role="Responder-A", model="gpt-4o-mini"),
            Participant(role="Responder-B", model="llama3-70b"),
        ],
    )
)


# --- Helpers ----------------------------------------------------------------

def _filter_topics(status: Optional[str]) -> List[Topic]:
    if status is None:
        return topics
    return [t for t in topics if t.status == status]


def _filter_sessions(state: Optional[str]) -> List[Session]:
    if state is None:
        return sessions
    return [s for s in sessions if s.state == state]


def _get_topic(topic_id: str) -> Topic:
    for topic in topics:
        if topic.id == topic_id:
            return topic
    raise HTTPException(status_code=404, detail="Topic not found")


def _get_session(session_id: str) -> Session:
    for session in sessions:
        if session.id == session_id:
            return session
    raise HTTPException(status_code=404, detail="Session not found")


# --- Routes -----------------------------------------------------------------

@app.post("/topics", response_model=Topic, status_code=201)
def create_topic(payload: TopicCreate) -> Topic:
    topic_id = f"topic_{len(topics) + 1:03d}"
    topic = Topic(id=topic_id, **payload.dict())
    topics.append(topic)
    return topic


@app.get("/topics")
def list_topics(status: Optional[TopicStatus] = None) -> dict:
    data = _filter_topics(status)
    # sort by votes descending then submitted_at descending
    data = sorted(data, key=lambda t: (t.votes, t.submitted_at), reverse=True)
    return {"items": data, "total": len(data)}


@app.post("/topics/{topic_id}/vote")
def vote_topic(topic_id: str, request: VoteRequest) -> dict:
    topic = _get_topic(topic_id)
    topic.votes += request.delta
    if topic.votes < 0:
        topic.votes = 0
    return {"id": topic.id, "votes": topic.votes}


@app.get("/sessions")
def list_sessions(state: Optional[SessionState] = None) -> dict:
    data = _filter_sessions(state)
    data = sorted(data, key=lambda s: s.scheduled_for, reverse=True)
    return {"items": data, "total": len(data)}


@app.get("/sessions/active")
def list_active_sessions() -> dict:
    data = _filter_sessions("active")
    return {"items": data, "total": len(data)}


@app.post("/sessions", status_code=202)
def create_session(payload: SessionCreate) -> dict:
    topic = _get_topic(payload.topic_id)
    session_id = f"session_{len(sessions) + 1:03d}"
    session = Session(
        id=session_id,
        topic_id=topic.id,
        title=topic.title,
        scheduled_for=payload.scheduled_for,
        state="upcoming",
        format=payload.format_id,
        participants=[
            Participant(role="Facilitator", model="claude-3-5-sonnet"),
            Participant(role="Expert-A", model="gpt-4o"),
            Participant(role="Expert-B", model="gemini-1.5-flash"),
        ],
    )
    sessions.append(session)
    topic.status = "scheduled"
    return {"id": session_id, "state": session.state}


# Optional: pseudo stream endpoint
@app.get("/sessions/{session_id}/stream")
def stream_session(session_id: str, since: Optional[datetime] = None) -> dict:
    """Return mock transcript chunks.

    In a real implementation this would pull incremental logs. Here we just
    return a fixed set of example messages.
    """

    _get_session(session_id)  # ensure it exists
    now = datetime.now(tz=UTC)
    messages = [
        {
            "timestamp": (now - timedelta(minutes=2)).isoformat(),
            "speaker": "Facilitator",
            "text": "Welcome to the AI round table on disaster response!",
        },
        {
            "timestamp": (now - timedelta(minutes=1)).isoformat(),
            "speaker": "Responder-A",
            "text": "Priority is improving data pipelines for rapid assessment.",
        },
        {
            "timestamp": now.isoformat(),
            "speaker": "Responder-B",
            "text": "We also need training for local responders leveraging AI tools.",
        },
    ]

    if since:
        messages = [m for m in messages if datetime.fromisoformat(m["timestamp"]) > since]

    return {"items": messages}


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/openapi.yaml", include_in_schema=False)
def openapi_spec() -> FileResponse:
    return FileResponse("../openapi.yaml", media_type="application/yaml")
