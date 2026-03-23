"""L6: Agent listing, detail, and conversation.

Tests against the real agent-factory and agent-app services.
"""

from __future__ import annotations

import pytest

from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_list_agents(kweaver_client: KWeaverClient):
    """List agents should return without error."""
    agents = kweaver_client.agents.list()
    assert isinstance(agents, list)


def test_list_agents_published(kweaver_client: KWeaverClient):
    """Published filter should only return published agents."""
    agents = kweaver_client.agents.list(status="published")
    assert isinstance(agents, list)
    for a in agents:
        assert a.status == "published"


@pytest.fixture(scope="module")
def any_agent(kweaver_client: KWeaverClient):
    """Create a temporary agent for read tests, delete on teardown."""
    # Discover LLM model (required for agent creation)
    http = kweaver_client._http
    try:
        data = http.get("/api/mf-model-manager/v1/llm/list", params={"page": 1, "size": 100})
    except Exception:
        pytest.skip("model-factory not available")
    models = (data or {}).get("data", [])
    llm = next((m for m in models if m.get("model_type") == "llm"), None)
    if not llm:
        pytest.skip("no LLM model available")

    config = {
        "input": {"fields": [{"name": "user_input", "type": "string", "desc": ""}]},
        "output": {"default_format": "markdown"},
        "system_prompt": "E2E read test agent",
        "llms": [{"is_default": True, "llm_config": {
            "id": llm["model_id"], "name": llm["model_name"],
            "model_type": "llm", "max_tokens": 4096,
        }}],
    }

    result = kweaver_client.agents.create(
        name="e2e_read_test_agent",
        profile="E2E test agent for read operations",
        key="e2e_read_test_key",
        config=config,
    )
    agent_id = result.get("id") if isinstance(result, dict) else result.id
    agent = kweaver_client.agents.get(agent_id)
    yield agent
    try:
        kweaver_client.agents.delete(agent_id)
    except Exception:
        pass


def test_get_agent(kweaver_client: KWeaverClient, any_agent):
    """Get agent detail should return full config."""
    agent = kweaver_client.agents.get(any_agent.id)
    assert agent.id == any_agent.id
    assert agent.name == any_agent.name


def test_agent_has_fields(kweaver_client: KWeaverClient, any_agent):
    """Agent detail should contain key fields from agent-factory."""
    agent = kweaver_client.agents.get(any_agent.id)
    assert agent.id
    assert agent.name
    assert agent.status in ("published", "draft")
    # version and system_prompt come from detail endpoint
    assert agent.version is not None or agent.system_prompt is not None


@pytest.mark.destructive
def test_conversation_flow(kweaver_client: KWeaverClient):
    """Create conversation, send message, verify response.

    Tries all published agents until one responds successfully.
    Fails if no published agent can produce a valid response.
    """
    agents = kweaver_client.agents.list(status="published")
    assert agents, "No published agents found"

    errors: list[tuple[str, Exception]] = []
    for agent in agents:
        conv = kweaver_client.conversations.create(agent.id)
        assert conv.agent_id == agent.id

        try:
            reply = kweaver_client.conversations.send_message(
                conv.id,
                content="你好",
                agent_id=agent.id,
                agent_version=agent.version or "latest",
            )
            assert reply.content
            assert reply.role == "assistant"
            return  # success — at least one agent works
        except Exception as e:
            errors.append((agent.name, e))
            continue  # try next agent

    error_details = "; ".join(f"[{name}] {e}" for name, e in errors)
    pytest.fail(
        f"All {len(agents)} published agents failed: {error_details}"
    )
