# Terminal Engine Roadmap

## Short-Term (Visual Cursor Support)

- Detect reverse-video highlights emitted by Gemini/Claude and treat them as
  the active cursor in ActCLI-Bench (implemented in `term_emulator.py`).
- Guard the behaviour with automated tests (see `tests/unit/test_term_emulator_cursor.py`).
- Keep the pyte fork plan on standby only if additional ANSI-level issues
  surface that the hybrid approach cannot cover.

## Medium-Term (ActCLI-TE)

- Build ActCLI-TE, our MIT-licensed terminal engine based on the Rust `vte`
  parser. Project scaffolding lives in `ActCLI-TE/` and will graduate to its
  own repository in the ActCLI org.
- Integrate ActCLI-TE behind a feature flag in ActCLI-Bench so we can dogfood
  it and compare output with the patched `pyte` backend.
- Once parity is confirmed, flip the default to ActCLI-TE and drop the `pyte`
  dependency.

## Long-Term (Hosted & Browser Clients)

- Reuse ActCLI-TE in both local Textual apps and future browser-based UIs
  (xterm.js front end) powered by the facilitator service.
- Consolidate diagnostics and logging around the new engine to simplify
  troubleshooting across deployment modes.
