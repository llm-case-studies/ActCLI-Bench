# Terminal Engine Roadmap

## Short-Term (Patch pyte)

- Carry a minimal fork of `pyte` with the cursor-position fix so Textual users
  have a reliable experience immediately.
- Publish the fork as `pyte-0.8.2+actcli` (still LGPL) and document the
  dependency in release notes.
- Add regression fixtures to ensure the patched behavior stays intact while we
  work on the long-term solution.

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

