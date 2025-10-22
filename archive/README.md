# Archive - Legacy Prototypes

This directory contains early prototype code that is no longer actively maintained.

## What's Here

### legacy_prototypes/

Contains the original prototype implementations that were superseded by `bench_textual`:

1. **wrapper_tui/** - Prompt Toolkit-based TUI (deprecated)
   - `shell.py` - Original TUI shell using prompt_toolkit
   - `terminal_tab.py` - Terminal tab management
   - `wrapped_terminal.py` - PTY wrapper for terminals
   - `session_manager.py` - Session management (moved to bench_textual)

2. **wrapper/** - Standalone PTY wrapper and CLI tools (deprecated)
   - `wrap_cli.py` - PTY wrapper CLI
   - `pty_wrapper.py` - PTY process wrapper
   - `cli.py` - CLI utilities
   - `client.py` - Facilitator client (moved to bench_textual)
   - `facilitator_cli.py` - Facilitator server CLI

3. **facilitator/** - Multi-user session server (deprecated)
   - `service.py` - FastAPI-based session service
   - `session.py` - Session management

## Why Archived?

These were experimental prototypes developed during the early stages of ActCLI-Bench.
The project has since standardized on **bench_textual** as the primary TUI implementation,
which uses Textual framework instead of prompt_toolkit and provides:

- Better terminal emulation (VT100 via pyte)
- Cleaner architecture
- Better test coverage
- More maintainable codebase

## Active Code

The actively maintained code is in:
- `src/actcli/bench_textual/` - Main TUI application
- Entry point: `actcli-bench` command

## History

- Oct 2024: Initial prototypes (wrapper, wrapper_tui, facilitator)
- Oct 21, 2024: Archived prototypes, standardized on bench_textual
