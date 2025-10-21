  ActCLI‑Bench — Status and Next Steps

  - Status date: 2025‑10‑20 (refreshed after completing Phases 0 & 1)
  - Repo: this repository (ActCLI‑Bench)
  - Active branch in recent work/screenshots: feat/bench‑emulator‑rebased

  Branches (to confirm exactly)

  - Known/observed:
      - main — default branch
      - feat/bench-emulator-rebased — Textual bench, emulator, width/scrollback work
  - Please confirm the complete inventory and remote URLs (read‑only, safe):
      - git status -sb
      - git branch -a -vv
      - git remote -v
  - Paste those outputs below to lock this doc to facts.

  Other Repositories Considered

  - None. All relevant pieces (Textual bench UI, facilitator client/service, wrappers) are under src/actcli/* here.
  - If you use separate facilitator/viewer repos, list them here with their roles; otherwise, this plan is repo‑local.

  Current State Summary

  - Textual bench runs with:
      - Tree navigation: Terminals, Sessions, Settings, Logs
      - Terminal view (VT emulation via pyte when available), scrollback, focusable pane
      - Control pad to broadcast; optional mirror to viewer
      - Logging via LogManager (Events, Errors, Output, Debug)
  - Observability improvements (Phase 0) in place:
      - Header banner now shows session/viewer plus actcli, textual, pyte versions and active emulator mode.
      - Emulator instantiation logs once per terminal whether pyte is active, and KEY→PTY writes land in Debug.
      - Bench version bumped to 0.0.3 and surfaced as `actcli-bench` in the title bar; terminal border now briefly highlights on startup or when opening the troubleshooting log so you can confirm fresh builds at a glance.
      - New "Troubleshooting Pack" log/export (with timestamped snapshots) makes it easy to capture runtime context for support.
  - Terminal width behavior:
      - PTY child now receives a 48×240 winsize before exec; parent schedules resizes at 50/200/500/1000 ms to catch layout adjustments.
      - UI still synchronizes pane→emulator→PTY immediately, preventing the “narrow until scroll” startup glitch.
      - Ongoing issue: Gemini/Claude/bash still render narrow until a later redraw (mouse-wheel scroll or layout change). See Experiments & Observations below.
  - Facilitator bootstrap:
      - When the facilitator or default session is unavailable, the bench now logs the exception and continues (no viewer URL).
  - Input behavior:
      - Reports of “typing not working” in the terminal pane. Needs robust key→PTY mapping and a clear focus signal.
  - Copy/selection:
      - Copying strings out of the bench is still tricky (terminal pane text not selectable); screenshots are a workaround for now.

  What Should Be Done In This Repo

  - Strengthen input routing
      - Forward printable characters even when event.character is absent (fallback to event.key).
      - Map control keys (Enter/Return, Backspace, arrows, PageUp/Down, Home/End; optionally Ctrl‑C/D).
      - Ensure terminal pane auto‑focus on activation; make focus state obvious.
  - Copy support
      - Settings → “Copy viewer URL”: copy to clipboard when available; always also place into the bottom input and focus it for easy selection.
  - Tree UX polish and cleanup
      - Finish Tree actions (Add…, Connect…, Mute/Unmute All, Mirror toggle) and reflect states in nav labels.
      - Remove legacy ListView/compact logs code paths and unused CSS.
  - Tests and docs
      - Tests: winsize pre‑exec + post‑render sync behavior; key mapping for common keys.
      - Docs: quickstart, controls, copy options, troubleshooting.

  Proposed Implementation Plan (Phased)

  - Phase 0 — Observability ✅ (header banner, emulator mode logging, KEY→PTY debug)
  - Phase 1 — Width at startup ✅ (pre-exec winsize + staged resizes)
  - Phase 2 — Input robustness
      - Printable key fallback from event.key; control key mapping; auto‑focus on activation.
      - Acceptance: typing echoes (for echo‑on apps); arrow/page keys navigate; Debug shows KEY→PTY logs.
  - Phase 3 — Copy support
      - Settings action to make the viewer URL trivially copyable (clipboard when available; always populate the bottom input).
      - Acceptance: user can copy the URL without screenshots.
  - Phase 4 — Cleanup + tests
      - Remove legacy nav/log code; add winsize + key mapping tests; update docs.

  Specs / Acceptance Criteria

  - Version banner: renders actcli/textual/pyte versions and mode. If pyte isn’t importable, pyte shows “none” and mode is “plain”. ✅
  - Emulator mode logging: exactly one Debug/Events line per terminal indicating mode. ✅
  - Startup width: child receives non‑80×24 winsize prior to first output; UI resizes keep emulator and PTY in sync. No “narrow → wide only after scroll”. ✅
  - Input routing: printable + control keys work; KEY→PTY logs appear for each write; terminal pane clearly indicates focus state.
  - Copy support: Settings action populates bottom input with the URL and focuses it; clipboard copy used when available.
  - Cleanup: Tree is the only nav; no references to removed list/log code; CSS only for current widgets.
  - Facilitator fallback: bench remains usable even if facilitator/session creation fails; Events log records the issue.

  Notes on Terminal Width Issue

  - Historic reference for the investigation lived in /home/alex/Projects/ActCLI-Bench/TERMINAL_WIDTH_ISSUE.md.
  - Current implementation now sets the winsize before exec and re-syncs shortly after mount; keep that doc for background if regressions appear.

  Execution Order

  - Phase 0 instrumentation
  - Phase 1 startup width + staged resizes
  - Phase 2 input robustness
  - Phase 3 copy support
  - Phase 4 cleanup + tests

  Risk and Observability

  - PTY sizing uses standard ioctl and SIGWINCH; log effective sizes to verify.
  - Key path changes are additive (fallbacks + logs). If a key doesn’t echo, Debug will confirm whether it reached the PTY.
  - All work scoped to bench UI/runner; facilitator unaffected.

  Open Questions

  - Should we send a benign newline on first activation to force some TUIs to redraw at the new width? (Toggle: “Auto newline on activation”.)
  - Do we want clipboard integration beyond the bottom‑input fallback (e.g., optional pyperclip)?
  - How can we reliably trigger an early redraw (without user scroll) for prompt_toolkit-based CLIs?

  Experiments & Observations (2025-10-20)

  - PTY sizing diagnostics:
      - `winsize_history` logs and `runner.get_winsize` confirm that every resize request lands; `stty size` in bash reports the full width immediately (e.g., `39 173`).
      - The delayed 0.5s redraw still results in narrow renders, which means the CLIs ignore SIGWINCH while initializing.
  - User interaction experiments:
      - Mouse wheel scrolling (after the terminal view is focused) always forces an immediate redraw to the correct width.
      - Touchpad gestures and key-up/down do not trigger a redraw—likely different event paths, so `_schedule_terminal_resizes` never runs.
      - Resizing the outer terminal proportionally scales the narrow layout but does not trigger a wider redraw.
      - Switching to Troubleshooting (or scrolling the view) unfocuses/refocuses the terminal and calls `_schedule_terminal_resizes`, which indirectly fixes the width once the CLI is idle.
  - Snapshot workflow:
      - Troubleshooting Pack exports live under `docs/Trouble-Snaps/troubleshooting_pack_<timestamp>.txt`. Each pack now includes winsize history, first-output previews, recent key events, and a `writer_attached` flag.
      - Collect snapshots immediately after launching, after typing (without scrolling), and after scrolling to see how PTY state, key events, and redraws align.
      - Version indicator bumped to 0.0.3; the terminal border blinks briefly on startup or when the Troubleshooting log is opened to confirm a fresh build.
  - Current hypothesis:
      - prompt_toolkit (and our nested Textual bench) renders the splash with the 80-column default and does not process the early resize until idle. We need an automated late redraw—likely by resending SIGWINCH (and possibly simulating a focus change) once the prompt is ready.
