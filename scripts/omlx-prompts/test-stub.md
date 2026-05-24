Write a Python pytest file `<<test_filename.py>>`. Output Python code only. No markdown fences. No commentary.

Module docstring: """Tests for <<module under test>>."""

Imports:
    from __future__ import annotations
    import pytest
    from <<module under test>> import <<symbols>>
    <<additional imports>>

For each public function below, generate:
- one happy-path test (typical input → expected output)
- one boundary test (min/max valid input)
- one error test (invalid input → expected exception)

Use `pytest.raises(<<ExceptionType>>, match=r"<<regex>>")` for error cases.
Use `monkeypatch` for any I/O / model-call dependencies — never let tests
hit the network or load real ML models.

Functions to test:

1. `<<func_signature>>`
   I/O examples:
     <<func>>(<<args>>) -> <<output>>
     <<func>>(<<args>>) -> raises <<Exception>>

2. `<<func_signature>>`
   I/O examples:
     <<...>>

<<repeat for each function>>

No fixtures with side effects. No real DB / file writes outside `tmp_path`.
Tests must be runnable with: `pytest <<test_filename.py>>`.
