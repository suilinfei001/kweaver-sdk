"""Unit tests for CLI agent commands using Click's CliRunner."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
from click.testing import CliRunner

from kweaver.cli.main import cli
from tests.conftest import RequestCapture, make_client


@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


def test_generate_timestamped_path_with_directory():
    """Test _generate_timestamped_path with directory input."""
    from kweaver.cli._helpers import _generate_timestamped_path

    result = _generate_timestamped_path("/tmp/config/")
    assert "/tmp/config/agent-config-" in result
    assert result.endswith(".json")


def test_generate_timestamped_path_with_file():
    """Test _generate_timestamped_path with file input."""
    from kweaver.cli._helpers import _generate_timestamped_path

    result = _generate_timestamped_path("/tmp/config.json")
    assert "/tmp/config-" in result
    assert result.endswith(".json")


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


def test_list_personal_agents_basic():
    """Test list_personal_agents with basic response."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"entries": [{"id": "a1", "name": "Test", "profile": "Desc"}]},
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "personal-list"])

    assert result.exit_code == 0
    assert "Test" in result.output


def test_list_personal_agents_with_keyword():
    """Test list_personal_agents with keyword filter."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        return httpx.Response(
            200,
            json={"entries": [{"id": "a1", "name": "SupplyAgent", "profile": "Supply chain"}]},
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "personal-list", "--keyword", "supply"])

    assert result.exit_code == 0
    assert call_count[0] > 0


def test_list_categories_basic():
    """Test list_categories with basic response."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [{"id": "c1", "name": "分类1"}]})

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "category-list"])

    assert result.exit_code == 0
    assert "分类1" in result.output


def test_list_categories_verbose():
    """Test list_categories with verbose output."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "entries": [
                    {"id": "c1", "name": "分类1", "description": "Category description"}
                ]
            },
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "category-list", "--verbose"])

    assert result.exit_code == 0
    assert "分类1" in result.output


def test_template_list_basic():
    """Test template_list with basic response."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"entries": [{"id": "t1", "name": "Template1", "profile": "Desc"}]},
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "template-list"])

    assert result.exit_code == 0
    assert "Template1" in result.output


def test_template_list_with_filters():
    """Test template_list with category and keyword filters."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        return httpx.Response(
            200,
            json={"entries": [{"id": "t1", "name": "FilteredTemplate", "profile": "Desc"}]},
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(
                cli,
                ["agent", "template-list", "--category-id", "cat1", "--keyword", "filter"],
            )

    assert result.exit_code == 0
    assert call_count[0] > 0


def test_template_get_save_config():
    """Test template_get with --save-config option."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "tpl_id": "t1",
                "name": "Template1",
                "description": "Desc",
                "config": {"key": "value"},
            },
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / "config.json"
                result = runner.invoke(
                    cli, ["agent", "template-get", "t1", "--save-config", str(config_path)]
                )

                assert result.exit_code == 0, f"Command failed: {result.output}"
                saved_path = result.output.strip()
                # Verify file was created with timestamp
                assert "config-" in saved_path
                # Verify the file exists and contains the config (check inside tmpdir context)
                assert Path(saved_path).exists(), f"File not found: {saved_path}"
                import json

                with open(saved_path) as f:
                    saved_config = json.load(f)
                assert saved_config == {"key": "value"}


def test_template_get_verbose():
    """Test template_get with --verbose option."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "tpl_id": "t1",
                "name": "Template1",
                "profile": "Desc",
                "config": {"key": "value"},
            },
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "template-get", "t1", "--verbose"])

    assert result.exit_code == 0
    assert "Template1" in result.output


def test_template_get_basic():
    """Test template_get with basic output."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "tpl_id": "t1",
                "name": "Template1",
                "profile": "Desc",
                "config": {"key": "value"},
            },
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "template-get", "t1"])

    assert result.exit_code == 0
    assert "Template1" in result.output
    assert "key" in result.output


def test_update_with_knowledge_network_id():
    """Test update_agent with --knowledge-network-id option."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        if call_count[0] == 1:
            # First call is GET current agent
            return httpx.Response(
                200,
                json={"id": "a1", "name": "Test", "config": {}},
            )
        # Second call is UPDATE
        return httpx.Response(200, json={})

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(
                cli, ["agent", "update", "a1", "--knowledge-network-id", "kn_01"]
            )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_update_with_name():
    """Test update_agent with --name option."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        if call_count[0] == 1:
            return httpx.Response(
                200,
                json={"id": "a1", "name": "OldName", "profile": "", "config": {}},
            )
        return httpx.Response(200, json={})

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "update", "a1", "--name", "NewName"])

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_update_with_system_prompt():
    """Test update_agent with --system-prompt option."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        if call_count[0] == 1:
            return httpx.Response(
                200,
                json={"id": "a1", "name": "Test", "profile": "", "config": {}},
            )
        return httpx.Response(200, json={})

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(
                cli, ["agent", "update", "a1", "--system-prompt", "You are a helpful assistant"]
            )

    assert result.exit_code == 0


def test_update_with_config_path():
    """Test update_agent with --config-path option."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        if call_count[0] == 1:
            return httpx.Response(
                200,
                json={"id": "a1", "name": "Test", "profile": "", "config": {}},
            )
        return httpx.Response(200, json={})

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            with tempfile.TemporaryDirectory() as tmpdir:
                config_file = Path(tmpdir) / "config.json"
                import json

                config_file.write_text(json.dumps({"key": "value"}))
                result = runner.invoke(
                    cli, ["agent", "update", "a1", "--config-path", str(config_file)]
                )

    assert result.exit_code == 0


def test_update_with_multiple_options():
    """Test update_agent with multiple options combined."""
    call_count = [0]

    def handler(req: httpx.Request) -> httpx.Response:
        call_count[0] += 1
        if call_count[0] == 1:
            return httpx.Response(
                200,
                json={"id": "a1", "name": "OldName", "profile": "", "config": {}},
            )
        return httpx.Response(200, json={})

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(
                cli,
                [
                    "agent",
                    "update",
                    "a1",
                    "--name",
                    "NewName",
                    "--profile",
                    "New profile",
                    "--system-prompt",
                    "New prompt",
                    "--knowledge-network-id",
                    "kn_01",
                ],
            )

    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_agent_get_with_config_no_save():
    """Test agent get without --save-config option (Agent model doesn't have config field)."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "a1",
                "name": "Agent1",
                "profile": "Desc",
                "status": "published",
                "kn_ids": ["kn1"],
                "config": {"key": "value"},
            },
        )

    runner = CliRunner()
    with make_client(handler) as client:
        with patch("kweaver.cli.agent.make_client", return_value=client):
            result = runner.invoke(cli, ["agent", "get", "a1"])

    assert result.exit_code == 0
    assert "Agent1" in result.output
