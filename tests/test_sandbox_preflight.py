from __future__ import annotations
import os
import importlib
import pytest

def test_preflight_blocks_localhost(monkeypatch):
    sg = importlib.import_module("javu_agi.runtime.sandbox_guard")
    # allowlist yang berbahaya → harus meledak
    monkeypatch.setenv("EGRESS_ALLOWLIST", "localhost,127.0.0.1")
    with pytest.raises(RuntimeError):
        sg.preflight()

def test_preflight_allows_public(monkeypatch):
    sg = importlib.import_module("javu_agi.runtime.sandbox_guard")
    # host publik aman
    monkeypatch.setenv("EGRESS_ALLOWLIST", "api.notion.com,graph.microsoft.com")
    assert sg.preflight() is True
