"""KWeaver SDK — CLI and client library for KWeaver knowledge networks."""

from __future__ import annotations

from typing import Iterator

from kweaver._auth import ConfigAuth, OAuth2Auth, OAuth2BrowserAuth, PasswordAuth, TokenAuth
from kweaver._client import KWeaverClient
from kweaver._errors import (
    KWeaverError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    ServerError,
    ValidationError,
)
from kweaver.types import (
    Agent,
    KnowledgeNetwork,
    Message,
    MessageChunk,
    SemanticSearchResult,
)

__all__ = [
    # Client
    "KWeaverClient",
    # Auth
    "TokenAuth",
    "PasswordAuth",
    "OAuth2Auth",
    "ConfigAuth",
    "OAuth2BrowserAuth",
    # Errors
    "KWeaverError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "NetworkError",
    "NotFoundError",
    "ServerError",
    "ValidationError",
    # Module-level API
    "configure",
    "search",
    "agents",
    "chat",
    "knowledge_networks",
]

# ── Global state ──────────────────────────────────────────────────────────────

_default_client: KWeaverClient | None = None
_default_kn_id: str | None = None
_default_agent_id: str | None = None


# ── configure() ───────────────────────────────────────────────────────────────

def configure(
    url: str,
    *,
    token: str | None = None,
    username: str | None = None,
    password: str | None = None,
    config: bool = False,
    kn_id: str | None = None,
    agent_id: str | None = None,
) -> None:
    """Initialize the default KWeaver client.

    Auth priority: token > username+password > config file.

    Args:
        url: KWeaver base URL, e.g. "https://kweaver.example.com".
        token: Bearer token for TokenAuth.
        username: Username for PasswordAuth (requires password).
        password: Password for PasswordAuth (requires username).
        config: If True, use credentials from the local config file.
        kn_id: Default knowledge network ID for search() calls.
        agent_id: Default agent ID for chat() calls.

    Example::

        import kweaver
        kweaver.configure("https://kweaver.example.com", token="my-token", kn_id="abc123")
    """
    global _default_client, _default_kn_id, _default_agent_id

    if token:
        auth = TokenAuth(token)
    elif username and password:
        auth = PasswordAuth(base_url=url, username=username, password=password)
    elif config:
        auth = ConfigAuth()
    else:
        raise ValueError("Provide token=, username+password=, or config=True")

    _default_client = KWeaverClient(base_url=url, auth=auth)
    _default_kn_id = kn_id
    _default_agent_id = agent_id


def _require_client() -> KWeaverClient:
    if _default_client is None:
        raise RuntimeError(
            "No KWeaver client configured. Call kweaver.configure() first."
        )
    return _default_client


# ── Top-level API functions ───────────────────────────────────────────────────

def search(
    query: str,
    *,
    kn_id: str | None = None,
    mode: str = "keyword_vector_retrieval",
    max_concepts: int = 10,
) -> SemanticSearchResult:
    """Semantic search on a knowledge network.

    Args:
        query: Natural-language search query.
        kn_id: Knowledge network ID. Falls back to the kn_id set in configure().
        mode: Retrieval mode (default "keyword_vector_retrieval").
        max_concepts: Maximum number of concepts to return.

    Example::

        results = kweaver.search("KWeaver 能做什么？")
        for concept in results.concepts:
            print(concept.concept_name)
    """
    client = _require_client()
    resolved_kn_id = kn_id or _default_kn_id
    if not resolved_kn_id:
        raise ValueError(
            "No kn_id provided. Pass kn_id= or set it in kweaver.configure()."
        )
    return client.query.semantic_search(
        resolved_kn_id, query, mode=mode, max_concepts=max_concepts
    )


def agents(
    *,
    keyword: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Agent]:
    """List agents.

    Args:
        keyword: Filter by name substring.
        status: Filter by status ("published" / "draft").
        limit: Maximum number of agents to return.

    Example::

        for agent in kweaver.agents(status="published"):
            print(agent.name)
    """
    client = _require_client()
    return client.agents.list(keyword=keyword, status=status, limit=limit)


def chat(
    message: str,
    *,
    agent_id: str | None = None,
    stream: bool = False,
    conversation_id: str = "",
) -> Message | Iterator[MessageChunk]:
    """Send a message to an agent.

    Args:
        message: User message content.
        agent_id: Agent ID. Falls back to the agent_id set in configure().
        stream: If True, return an iterator of MessageChunk objects.
        conversation_id: Existing conversation ID (omit to start a new conversation).

    Example::

        reply = kweaver.chat("KWeaver 是什么？")
        print(reply.content)

        # Streaming
        for chunk in kweaver.chat("讲个故事", stream=True):
            print(chunk.delta, end="", flush=True)
    """
    client = _require_client()
    resolved_agent_id = agent_id or _default_agent_id
    if not resolved_agent_id:
        raise ValueError(
            "No agent_id provided. Pass agent_id= or set it in kweaver.configure()."
        )
    return client.conversations.send_message(
        conversation_id,
        message,
        agent_id=resolved_agent_id,
        stream=stream,
    )


def knowledge_networks(
    *,
    name: str | None = None,
    limit: int = 50,
) -> list[KnowledgeNetwork]:
    """List knowledge networks.

    Args:
        name: Filter by exact name.
        limit: Maximum number of results to return.

    Example::

        for kn in kweaver.knowledge_networks():
            print(kn.id, kn.name)
    """
    client = _require_client()
    return client.knowledge_networks.list(name=name, limit=limit)
