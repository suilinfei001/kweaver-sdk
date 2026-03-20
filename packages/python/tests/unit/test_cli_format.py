"""Tests for CLI output formatting."""
from __future__ import annotations

import json
import pytest

from kweaver.cli._helpers import output


def test_output_json(capsys):
    """--format json outputs valid JSON."""
    data = [{"id": "kn-1", "name": "test"}]
    output(data, format="json")
    captured = capsys.readouterr().out
    parsed = json.loads(captured)
    assert parsed == data


def test_output_md_list(capsys):
    """--format md outputs a markdown table for list data."""
    data = [{"id": "kn-1", "name": "test"}, {"id": "kn-2", "name": "demo"}]
    output(data, format="md")
    captured = capsys.readouterr().out
    assert "|" in captured
    assert "kn-1" in captured
    assert "kn-2" in captured


def test_output_md_dict(capsys):
    """--format md outputs key-value pairs for dict data."""
    data = {"id": "kn-1", "name": "test", "status": "active"}
    output(data, format="md")
    captured = capsys.readouterr().out
    assert "kn-1" in captured


def test_output_yaml_raises_without_pyyaml():
    """--format yaml without PyYAML should raise UsageError."""
    import unittest.mock as mock
    import click
    with mock.patch.dict("sys.modules", {"yaml": None}):
        with pytest.raises(click.UsageError, match="yaml"):
            output({"a": 1}, format="yaml")


def test_output_default_is_md(capsys):
    """Default format should be md."""
    data = [{"id": "1", "name": "x"}]
    output(data)
    captured = capsys.readouterr().out
    assert "|" in captured  # markdown table
