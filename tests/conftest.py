"""Shared pytest fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure src/ on sys.path for direct test runs without `pip install -e .`
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def corpus_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated corpus root for upload tests. Sets AISERVER_CORPUS_ROOT env."""
    root = tmp_path / "uploads"
    root.mkdir()
    monkeypatch.setenv("AISERVER_CORPUS_ROOT", str(root))
    return root


@pytest.fixture
def stub_models(monkeypatch: pytest.MonkeyPatch):
    """Block real model downloads in unit tests.

    Tests that need real model behaviour should override individual functions
    on the module under test. This fixture is a defence-in-depth guard.
    """
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    yield
