# ActCLI Round Table: Vision & Roadmap

## Overview
The ActCLI Round Table initiative turns our command-line bench into a recurring "AI reality show" where multiple agent personas debate viewer-submitted topics. The long-term goal is to run these sessions on a fixed schedule, surface them through a public-facing site, and archive the outputs as a living knowledge base.

## Goals
- **Recurring public round tables** – run one or two sessions per day featuring 3–4 AI participants and an AI facilitator.
- **Viewer participation** – accept topic submissions, queue them with basic moderation, and let the community vote priorities.
- **Rich session context** – auto-generate topic dossiers (summaries, reference articles, prior transcripts) so discussions stay factual and engaging.
- **Transparent archives** – publish transcripts, summaries, and (optionally) audio/video to an accessible library.
- **Operational automation** – schedule sessions, kick off the bench with configuration files, gather artifacts, and update the frontend with minimal manual steps.

## Session Lifecycle
1. **Topic intake & moderation**
   - Viewers submit topics via the public portal.
   - Automated filters catch profanity, spam, or duplicates.
   - (Optional) Human Moderators approve borderline cases.

2. **Queue & scheduling**
   - Approved topics enter a priority queue (weighted by votes, freshness, or manual overrides).
   - Scheduler pulls the highest-ranked topics based on the daily run cadence.

3. **Preparation**
   - Generate a *topic dossier* with summary context, references, and any viewer-provided materials (converted to text).
   - Select a **format** (e.g., consensus round table, pro/con debate) and load a YAML config containing roles, rounds, and prompts.
   - Provision temporary storage for session artifacts (transcripts, troubleshooting packs, audio).

4. **Live session**
   - Bench starts with the chosen participants (CLI wrappers or OSS models) and facilitator instructions.
   - Session engine enforces the format: turn order, round limits, facilitator checkpoints.
   - Optional: record audio via text-to-speech and mirror exchanges to a live viewer tab.

5. **Post-processing**
   - Generate structured outputs: cleaned transcript, summary, key takeaways, highlight reel.
   - Produce derived artifacts (PDF, Markdown, JSON) and attach metadata (topic, date, participants, model versions).
   - Store results in the archive and notify the frontend to refresh the archive list.

6. **Analytics & feedback**
   - Capture engagement metrics (votes, views, dwell time).
   - Collect viewer feedback for future sessions (optional form or social embeds).

## Technical Pillars
- **Bench Extensions**
  - Format loader (YAML/JSON) to configure participants, prompts, and turn order.
  - Session orchestrator to manage rounds, prompts, and artifact production.
  - Context packager to bundle dossier files into each session directory.
  - Optional: text-to-speech integration and audio asset pipeline.

- **Public Frontend & API**
  - Topic submission & voting UI.
  - Live viewer with session metadata, restreamed text/audio, and countdown timers.
  - Archive browser with filtering, search, and downloadable assets.
  - REST API for queue/topic/session management with secure tokens for the scheduler.

- **Scheduler & Automation**
  - Cron or serverless tasks that:
    1. Pull top topics from the queue.
    2. Generate dossiers & format configs.
    3. Trigger bench sessions.
    4. Capture outputs and update the frontend archive.

- **Data & Storage**
  - Relational DB (SQLite/Postgres) for topics, votes, sessions, participants.
  - Object storage (S3/GCS/minio) for transcripts, packs, audio/video, and generated PDFs.
  - Logging stack to monitor pipeline health and capture postmortems.

## Roadmap
1. **Prototype Phase (Private)**
   - Stabilize bench (width/input fixes, artifact exports).
   - Create format configs & dossier pipeline.
   - Build a mock API + local frontend for topic submission and session scheduling.
   - Run manual sessions and collect results.

2. **Public Beta**
   - Deploy frontend POC (Google AI Studio-generated UI or custom React).
   - Integrate scheduler that kicks off at least one session daily.
   - Add live viewer tab (text + optional audio) and archive list.

3. **Launch & Iteration**
   - Harden moderation (user auth, abuse reporting).
   - Add search + filter in archive.
   - Explore monetization or sponsorship integrations (optional).
   - Expand to video streaming/YouTube or podcast distribution if desired.

## Open Questions
- Automatic redraw/wide layout behavior for participants (pending fix on the bench).
- Best format cadence (daily? weekly? themed tracks?).
- Whether to include human co-moderators or audience Q&A segments.
- Audio pipeline costs and latency vs. perceived value.
- Legal/licensing for public archives (model terms of use, user consent).

## Next Steps
- Finalize backend API schema (mock implementation below).
- Build the Google AI Studio POC against the mock API.
- Stress-test scheduling with the bench once the width fix lands.
- Collect ideas from other AIs / stakeholders and roll them into v1 requirements.

## Mock Backend (for Frontend Testing)
- Location: `ActCLI-Round-Table/mock_backend`.
- Install deps: `python3 -m venv .venv && source .venv/bin/activate && pip install -r ActCLI-Round-Table/mock_backend/requirements.txt`.
- Run: `uvicorn main:app --reload --app-dir ActCLI-Round-Table/mock_backend --host 0.0.0.0 --port 8000`.
- API base URL: `http://localhost:8000/api` (used by the frontend spec).
