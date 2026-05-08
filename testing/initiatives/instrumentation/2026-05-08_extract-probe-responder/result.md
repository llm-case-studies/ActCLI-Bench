# Validation Result - Extract Probe Responder

- Validation host:
- Product branch:
- Product commit SHA:
- Validation branch:
- Validation commit SHA:
- Verdict: `PASS` / `PASS with findings` / `FAIL` / `BLOCKED`

## Checks Run

- `python3 -m pytest tests/bench_textual/test_probe_responder.py tests/bench_textual/test_terminal_manager_probe_responder.py -v`:
- `python3 -m pytest tests/bench_textual/test_app_integration.py -q`:
- static check for `_respond_to_dsr`:
- direct helper DSR response smoke:
- direct helper no-query smoke:
- direct helper non-pyte smoke:

## Evidence Files

- `evidence/00_commit.txt`
- `evidence/01_preflight.txt`
- `evidence/02_unit_tests_probe_responder.txt`
- `evidence/03_app_integration_regression.txt`
- `evidence/04_no_inline_dsr_helper.txt`
- `evidence/05_direct_dsr_response.txt`
- `evidence/06_no_query_noop.txt`
- `evidence/07_non_pyte_noop.txt`
- `evidence/08_cleanup.txt`

## Findings

-

## Host Safety Notes

-

## Recommendation

-
