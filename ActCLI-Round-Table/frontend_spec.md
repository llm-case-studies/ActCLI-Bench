# Frontend POC Specification (Google AI Studio)

This document describes the minimum feature set and API contract that the frontend prototype should implement. The goal is to let Google AI Studio (or any FE builder) scaffold a working interface against a mock backend while the real bench integration is in progress.

## 1. User Journeys

### 1.1 Submit a Topic
1. Visitor opens the site, sees a "Submit Topic" card.
2. They provide:
   - Title (max 120 chars)
   - Description / question (max 1,000 chars)
   - Optional context link
   - Checkbox agreeing to guidelines
3. On submit, the frontend calls `POST /topics`.
4. The UI shows a success message (topic pending moderation) or inline error (invalid input / rejected).

### 1.2 Vote on Topics
1. Visitor navigates to "Topic Queue" page (list view).
2. Each card shows title, short description, submission age, current vote count, status (Pending, Approved, Scheduled).
3. Visitor clicks an upvote button which issues `POST /topics/{topic_id}/vote`.
4. Vote count updates immediately (optimistic), reverts if the API rejects (one vote per IP/session).

### 1.3 View Upcoming Sessions
1. Visit "Schedule" page.
2. Display list/table of topics scheduled for future sessions with countdown or scheduled time.
3. Clicking a session card reveals details: participants, format, link to live viewer (if active).

### 1.4 Watch a Live Session (text-first)
1. When a session is active (`GET /sessions/active` returns data), show a "Live Now" banner.
2. Provide a viewer screen with:
   - Topic information and participants list.
   - Streaming transcript (poll `GET /sessions/{session_id}/stream?since=timestamp` every few seconds or use WebSocket fallback later).
   - Optional placeholder for future audio player.

### 1.5 Browse Archive
1. Archive page displays sessions sorted by most recent.
2. Each entry shows topic title, date, participants, summary snippet, and download links (PDF, JSON transcript, troubleshooting pack if available).
3. Filter by model, topic tag, date.

## 2. API Contract (Mock Backend)

Base URL: `http://localhost:8000/api`

### 2.1 Topics

#### POST /topics
Request body:
```json
{
  "title": "How can AI help with climate adaptation?",
  "description": "Discuss near-term, medium-term interventions and ethical considerations.",
  "context_link": "https://example.com/article",
  "submitter": "anonymous"  // optional
}
```
Responses:
- `201 Created` + topic payload with status `pending`
- `422 Unprocessable Entity` for validation errors

#### GET /topics
Query params: `status` (pending|approved|scheduled), `limit`, `offset`

Response:
```json
{
  "items": [
    {
      "id": "topic_123",
      "title": "AI and climate adaptation",
      "description": "Discuss near-term...",
      "context_link": "https://example.com/article",
      "status": "pending",
      "votes": 42,
      "submitted_at": "2025-10-20T18:22:00Z"
    }
  ],
  "total": 1
}
```

#### POST /topics/{topic_id}/vote
Request body:
```json
{ "delta": 1 }
```
Response: `200 OK` with updated vote count or `403` if duplicate vote blocked.

### 2.2 Sessions

#### GET /sessions
Query params: `state` (upcoming|active|completed)

Response (example for completed archive entry):
```json
{
  "items": [
    {
      "id": "session_456",
      "topic_id": "topic_123",
      "title": "AI and climate adaptation",
      "scheduled_for": "2025-10-21T17:00:00Z",
      "state": "completed",
      "format": "consensus-round-table",
      "participants": [
        {"role": "Facilitator", "model": "claude-3-5-sonnet"},
        {"role": "Expert-A", "model": "gpt-4o"},
        {"role": "Expert-B", "model": "gemini-1.5-flash"}
      ],
      "summary": "Panel reached consensus on...",
      "artifacts": {
        "pdf": "https://cdn.example.com/archive/session_456.pdf",
        "transcript": "https://cdn.example.com/archive/session_456.json",
        "troubleshooting_pack": "https://cdn.example.com/archive/session_456.txt"
      }
    }
  ]
}
```

#### GET /sessions/active
Returns either `{ "items": [] }` or the same payload as `GET /sessions` with `state='active'`.

#### POST /sessions
Used by the scheduler or future bench integration. For now the frontend POC does not call this endpoint, but the backend exposes it for end-to-end testing.
Request body:
```json
{
  "topic_id": "topic_123",
  "format_id": "consensus-round-table",
  "scheduled_for": "2025-10-21T17:00:00Z"
}
```
Response: `202 Accepted` with mock session id.

### 2.3 Stream Endpoint (optional enhancement)
`GET /sessions/{session_id}/stream?since=2025-10-20T18:22:00Z`
- Returns incremental transcript chunks sorted by timestamp.
- Frontend can poll every 3–5 seconds.

## 3. UI Components & Layout

- **Navigation**: top bar with links to Submit Topic, Queue, Schedule, Live, Archive.
- **Submit Topic Form**: card with inputs, validation feedback, success banner.
- **Queue Table/Cards**: list with vote button, status tags, infinite scroll or pagination.
- **Schedule View**: list with countdown timers (use JavaScript client to compute relative time).
- **Live Viewer**: responsive layout with topic info sidebar and transcript panel (auto-scroll to bottom while session active).
- **Archive Grid**: cards showing summaries and download links.
- **Footer**: disclaimers, contact, “powered by ActCLI Bench” note.

## 4. Styling & UX Guidelines
- Modern, clean aesthetic (light theme by default). Provide open slots for branding later.
- Ensure mobile responsiveness (submit/vote/archive should work on phones).
- Provide loading states and empty-state messages (e.g., “No sessions live right now”).
- Use toasts/modal dialogs sparingly; prefer inline feedback.

## 5. Authentication & Rate Limits
- MVP: anonymous interactions with simple per-IP vote limit enforced by backend (mock service returns 403 when limit exceeded).
- Future: add user accounts/social login (placeholder button or disabled menu item for now).

## 6. Integration Notes
- The mock backend (FastAPI) will run locally on `http://localhost:8000/api` with Swagger docs.
- When the real bench integration is ready, the same endpoints will proxy actual data. The frontend should rely solely on this contract so the swap is seamless.

## 7. Deliverables for POC
1. Static build or deployable SPA that runs against the mock API and demonstrates all user journeys above.
2. Minimal documentation (README) describing how to run the frontend locally and how to point it to a different API base URL.
3. Optional: screenshot or short screencast showing the Submit/Vote/Live/Archive flows.

