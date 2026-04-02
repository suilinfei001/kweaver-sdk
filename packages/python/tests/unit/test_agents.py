"""Tests for agents resource (agent-factory v3 API)."""

import json

import httpx

from tests.conftest import RequestCapture, make_client


def _agent_list_json(**overrides):
    """Simulates agent-factory /published/agent response item."""
    base = {
        "id": "agent_01",
        "key": "key_01",
        "name": "供应链助手",
        "profile": "供应链领域问答",
        "version": "v5",
        "status": "published",
        "is_built_in": 0,
    }
    base.update(overrides)
    return base


def _agent_detail_json(**overrides):
    """Simulates agent-factory /agent/{id} response."""
    base = {
        "id": "agent_01",
        "key": "key_01",
        "name": "供应链助手",
        "profile": "供应链领域问答",
        "version": "v5",
        "status": "published",
        "config": {
            "system_prompt": "你是供应链专家",
            "data_source": {
                "kg": [{"kg_id": "kn_01", "fields": []}],
            },
            "llms": [{"is_default": True, "llm_config": {"name": "deepseek_v3"}}],
        },
    }
    base.update(overrides)
    return base


def test_list_agents():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [_agent_list_json()]})

    client = make_client(handler)
    agents = client.agents.list()
    assert len(agents) == 1
    assert agents[0].id == "agent_01"
    assert agents[0].name == "供应链助手"
    assert agents[0].status == "published"


def test_list_agents_with_filters(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": []})

    client = make_client(handler, capture)
    client.agents.list(keyword="供应链")
    body = capture.last_body()
    assert body["name"] == "供应链"
    assert "/published/agent" in capture.last_url()


def test_list_agents_with_offset_limit(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": []})

    client = make_client(handler, capture)
    client.agents.list(offset=10, limit=20)
    body = capture.last_body()
    assert body["offset"] == 10
    assert body["limit"] == 20


def test_list_agents_raw_list():
    """API returning a plain list (instead of {entries: [...]})."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[_agent_list_json()])

    client = make_client(handler)
    agents = client.agents.list()
    assert len(agents) == 1


def test_get_agent(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_agent_detail_json())

    client = make_client(handler, capture)
    agent = client.agents.get("agent_01")
    assert agent.id == "agent_01"
    assert agent.key == "key_01"
    assert agent.version == "v5"
    assert agent.system_prompt == "你是供应链专家"
    assert agent.kn_ids == ["kn_01"]
    assert "/agent/agent_01" in capture.last_url()


def test_get_agent_minimal_fields():
    """Agent with only required fields."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "a1", "name": "test"})

    client = make_client(handler)
    agent = client.agents.get("a1")
    assert agent.id == "a1"
    assert agent.status == "draft"
    assert agent.kn_ids == []
    assert agent.capabilities == []
    assert agent.conversation_count == 0


def test_status_mapping():
    """published_edited should map to published."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [
            _agent_list_json(status="published_edited"),
        ]})

    client = make_client(handler)
    agents = client.agents.list()
    assert agents[0].status == "published"


# ---------------------------------------------------------------------------
# Helper functions for new API methods
# ---------------------------------------------------------------------------


def _template_list_json(**overrides):
    """Simulates agent-factory /published/agent-tpl response item."""
    base = {
        "tpl_id": "tpl_01",
        "name": "合同审核助手模板",
        "profile": "合同审核领域问答",
        "config": {"key": "value"},
    }
    base.update(overrides)
    return base


def _category_json(**overrides):
    """Simulates agent-factory /category response item."""
    base = {
        "id": "cat_01",
        "name": "分类1",
        "description": "描述",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Tests for list_personal()
# ---------------------------------------------------------------------------


def test_list_personal_agents():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [_agent_list_json()]})

    client = make_client(handler)
    agents = client.agents.list_personal()
    assert len(agents) == 1
    assert agents[0].id == "agent_01"


def test_list_personal_agents_with_filters(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": []})

    client = make_client(handler, capture)
    client.agents.list_personal(keyword="test", size=10)
    assert "name=test" in capture.last_url()
    assert "size=10" in capture.last_url()


# ---------------------------------------------------------------------------
# Tests for list_templates()
# ---------------------------------------------------------------------------


def test_list_templates():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [_template_list_json()]})

    client = make_client(handler)
    templates = client.agents.list_templates()
    assert len(templates) == 1
    assert templates[0].id == "tpl_01"


def test_list_templates_with_filters(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": []})

    client = make_client(handler, capture)
    client.agents.list_templates(category_id="cat_01", keyword="test")
    assert "category_id=cat_01" in capture.last_url()
    assert "name=test" in capture.last_url()


# ---------------------------------------------------------------------------
# Tests for get_template()
# ---------------------------------------------------------------------------


def test_get_template(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_template_list_json())

    client = make_client(handler, capture)
    template = client.agents.get_template("tpl_01")
    assert template.id == "tpl_01"
    assert template.name == "合同审核助手模板"
    assert "/agent-tpl/tpl_01" in capture.last_url()


# ---------------------------------------------------------------------------
# Tests for list_categories()
# ---------------------------------------------------------------------------


def test_list_categories():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"entries": [_category_json()]})

    client = make_client(handler)
    categories = client.agents.list_categories()
    assert len(categories) == 1
    assert categories[0].id == "cat_01"


# ---------------------------------------------------------------------------
# Tests for publish() with category_id
# ---------------------------------------------------------------------------


def test_publish_with_category_id(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = make_client(handler, capture)
    client.agents.publish("agent_01", category_id="cat_01")
    body = capture.last_body()
    assert body["category_ids"] == ["cat_01"]
    assert body["business_domain_id"] == "bd_public"
