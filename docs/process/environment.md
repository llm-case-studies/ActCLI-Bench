# Host Environment Policy

This repo uses the sprint-pack process across multiple hosts. Environment
setup should make those handoffs repeatable without turning shared machines
into project-specific snow globes.

## Python Policy

Use shared, user-level Python virtual environments by stack, not system Python
and not mandatory per-repo `.venv` directories.

Recommended default for ActCLI Python work:

```bash
export ACTCLI_PYTHON_BIN="${ACTCLI_PYTHON_BIN:-python3}"
"$ACTCLI_PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("ActCLI-Bench requires Python >=3.10; set ACTCLI_PYTHON_BIN.")
PY

export ACTCLI_PY_ENV="${ACTCLI_PY_ENV:-$HOME/.venvs/actcli-python}"
"$ACTCLI_PYTHON_BIN" -m venv "$ACTCLI_PY_ENV"
. "$ACTCLI_PY_ENV/bin/activate"
python -m pip install -U pip
python -m pip install -e '.[textual,test]'
```

Rules:

- Use a Python binary compatible with the repo's `requires-python` setting.
- Do not install project dependencies into system Python for normal sprint
  work.
- Do not require every repo to carry its own `.venv` unless dependencies
  genuinely conflict.
- Keep dependency truth in repo metadata (`pyproject.toml`, lockfiles, or
  package manifests), then refresh the shared env from that metadata.
- If a shared env becomes conflicted, split it into a named stack env such as
  `$HOME/.venvs/actcli-bench-py313` and record that choice in the sprint pack
  or validation request.
- Validation evidence should record the env path, Python version, and key
  packages when dependency behavior matters.

This is intentionally reversible. If disk is plentiful or a repo needs hard
isolation, a sprint can opt into a repo-local `.venv`, but that should be an
explicit decision rather than the default.

## Node Policy

Node projects should follow their repo's package manager files and use the
normal user-level package cache. Do not invent Python virtualenv rules for
Node-only repos.

## Why Not System Python?

System Python belongs to the host OS and shared tooling. Mutating it to satisfy
one validation lane makes failures harder to explain for every other lane on
the same machine. A user-level shared env keeps disk use bounded while still
making project dependencies removable, refreshable, and inspectable.
