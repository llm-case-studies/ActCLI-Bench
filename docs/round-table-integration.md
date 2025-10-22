# Round Table Integration Specification

**Status:** 🚧 Planning Phase
**Last Updated:** 2025-10-22

## Overview

This document specifies how ActCLI-Bench will serve as the backend for the **ActCLI Round Table** public AI debate platform. The Round Table frontend needs ActCLI-Bench to:

1. Accept session requests from a scheduler
2. Execute multi-AI debate sessions with configurable formats
3. Stream live transcripts to viewers
4. Export structured artifacts (transcripts, metadata, audio)
5. Manage session state and provide status updates

## Architecture

```
┌─────────────────────┐
│  Round Table        │
│  Frontend + Viewer  │
└──────────┬──────────┘
           │ WebSocket/REST
           ↓
┌─────────────────────┐      ┌──────────────────┐
│  Scheduler          │─────→│  ActCLI-Bench    │
│  (Cron/Serverless)  │      │  REST API        │
└─────────────────────┘      └────────┬─────────┘
                                      │
                              ┌───────┴────────┐
                              │                │
                         ┌────▼────┐      ┌───▼────┐
                         │ Session │      │ Artifact│
                         │ Engine  │      │ Export  │
                         └─────────┘      └────────┘
```

## Required Components

### 1. REST API Server

**Not yet implemented** - Needs to be added to ActCLI-Bench.

**Technology options:**
- FastAPI (lightweight, async)
- Flask (simple, synchronous)
- Built into Textual app (experimental)

**Core endpoints:**

#### Session Management
- `POST /api/sessions` - Create and queue a session
- `GET /api/sessions/{id}` - Get session status
- `GET /api/sessions/{id}/stream` - Stream live transcript
- `DELETE /api/sessions/{id}` - Cancel a session
- `GET /api/sessions/active` - List currently running sessions

#### Artifacts
- `GET /api/sessions/{id}/artifacts` - List available artifacts
- `GET /api/sessions/{id}/transcript` - Download transcript (JSON/MD/PDF)
- `GET /api/sessions/{id}/metadata` - Get session metadata
- `GET /api/sessions/{id}/troubleshooting` - Download troubleshooting pack

### 2. Session Orchestrator

**Partially implemented** - Bench can run multiple terminals, but needs:
- Format configuration loader (YAML/JSON)
- Turn-based facilitation logic
- Round management
- Automatic prompt injection
- Participant coordination

**Format config example:**
```yaml
format: consensus_roundtable
participants:
  - role: facilitator
    model: claude-3-5-sonnet
    persona: neutral_moderator
  - role: participant
    model: gemini-2.0-flash
    persona: optimistic_futurist
  - role: participant
    model: gpt-4
    persona: pragmatic_skeptic
rounds:
  - name: opening_statements
    duration: 5min
    turn_order: sequential
  - name: cross_examination
    duration: 10min
    turn_order: facilitator_directed
  - name: synthesis
    duration: 5min
    facilitator_only: true
```

### 3. Transcript Streaming

**Needs implementation:**
- Real-time transcript capture from all participants
- WebSocket or Server-Sent Events for live updates
- Structured format with timestamps, speaker, content
- Buffer management for late viewers

**Stream format:**
```json
{
  "session_id": "session_abc123",
  "chunks": [
    {
      "timestamp": "2025-10-22T14:32:15Z",
      "speaker": "facilitator",
      "model": "claude-3-5-sonnet",
      "content": "Welcome to today's round table...",
      "chunk_id": 1
    },
    {
      "timestamp": "2025-10-22T14:33:01Z",
      "speaker": "participant_1",
      "model": "gemini-2.0-flash",
      "content": "I believe AI will...",
      "chunk_id": 2
    }
  ],
  "cursor": "2025-10-22T14:33:01Z"
}
```

### 4. Artifact Export

**Partially implemented** - Troubleshooting packs exist, but needs:
- Structured transcript export (JSON, Markdown, PDF)
- Session metadata file
- Participant information
- Topic context bundling
- Asset organization

**Artifact structure:**
```
sessions/
└── session_abc123/
    ├── metadata.json          # Session info, participants, timestamps
    ├── transcript.json        # Full structured transcript
    ├── transcript.md          # Human-readable markdown
    ├── transcript.pdf         # Formatted PDF (optional)
    ├── summary.md             # AI-generated summary
    ├── highlights.json        # Key moments, quotes
    ├── troubleshooting.zip    # Debug pack
    ├── topic/
    │   ├── dossier.md         # Topic context
    │   └── references.json    # Source links
    └── audio/                 # (Future) TTS recordings
        ├── facilitator.mp3
        ├── participant_1.mp3
        └── participant_2.mp3
```

## Integration Phases

### Phase 1: Core Session API (MVP)
**Goal:** Scheduler can trigger sessions and retrieve artifacts

- [ ] Implement basic REST API server
- [ ] Session creation endpoint
- [ ] Session status tracking
- [ ] Basic transcript capture
- [ ] JSON artifact export

**Deliverable:** Scheduler can create a session, monitor it, and download the transcript.

### Phase 2: Live Streaming
**Goal:** Viewers can watch sessions in real-time

- [ ] WebSocket or SSE implementation
- [ ] Live transcript streaming
- [ ] Session state broadcasts
- [ ] Viewer count tracking

**Deliverable:** Frontend can display live debates as they happen.

### Phase 3: Format Engine
**Goal:** Support different debate formats via configuration

- [ ] YAML format loader
- [ ] Turn management system
- [ ] Facilitator prompt injection
- [ ] Round transitions
- [ ] Time limits

**Deliverable:** Run "consensus", "debate", "interview" formats from config files.

### Phase 4: Rich Artifacts
**Goal:** Professional-quality outputs for archive

- [ ] PDF generation
- [ ] Summary generation (AI-powered)
- [ ] Highlight extraction
- [ ] Audio pipeline (TTS)
- [ ] Video generation (optional)

**Deliverable:** Archive has polished, shareable session records.

## API Specification Reference

See: `/home/alex/Projects/ActCLI-Round-Table/openapi.yaml`

Key endpoints ActCLI-Bench must implement:
- `POST /api/sessions` (from scheduler)
- `GET /api/sessions/{id}` (status check)
- `GET /api/sessions/{id}/stream` (live transcript)
- `GET /api/sessions/{id}/transcript` (download)
- `GET /api/sessions/active` (current sessions)

## Current Gaps

### High Priority
1. **No REST API** - Bench is a TUI app, needs HTTP server
2. **No session orchestration** - Can run terminals but not coordinate them
3. **No format configs** - Everything is manual

### Medium Priority
4. **No live streaming** - Can't send updates to viewers
5. **Limited artifact export** - Only troubleshooting packs
6. **No metadata capture** - Don't track participants, timestamps systematically

### Low Priority
7. **No audio pipeline** - TTS not integrated
8. **No summary generation** - Manual post-processing
9. **No authentication** - Anyone could trigger sessions

## Next Steps

1. **Decide on API architecture:**
   - Separate FastAPI service?
   - Embedded in Textual app?
   - Standalone HTTP server that controls bench?

2. **Design session orchestration:**
   - How to coordinate multiple AI terminals?
   - Turn management implementation
   - Prompt injection mechanism

3. **Define artifact format:**
   - Transcript schema
   - Metadata fields
   - Export pipeline

4. **Build MVP:**
   - Simple REST API
   - Basic session execution
   - JSON transcript export

## References

- Round Table Vision: `/home/alex/Projects/ActCLI-Round-Table/README.md`
- Frontend Spec: `/home/alex/Projects/ActCLI-Round-Table/frontend_spec.md`
- OpenAPI Spec: `/home/alex/Projects/ActCLI-Round-Table/openapi.yaml`
- Mock Backend: `/home/alex/Projects/ActCLI-Round-Table/mock_backend/`
