# KWeaver Python SDK

A clean Python interface for accessing KWeaver BKN (Business Knowledge Network) and Decision Agents.

[中文文档](README.zh.md)

## Installation

```bash
pip install kweaver-sdk
```

Requires **Python >= 3.10**.

## Quick Start

### Scenario 1: Read-only queries (connect to an existing BKN)

Use this mode when you only need to search or chat with an agent against an existing BKN. **No need to call `weaver()`.**

```python
import kweaver

kweaver.configure(
    url="https://kweaver.example.com",
    token="my-token",
    bkn_id="supply-chain-bkn-id",
    agent_id="supply-chain-agent-id",
)

# Semantic search over the BKN
results = kweaver.search("What are the key risks in the supply chain?")
for concept in results.concepts:
    print(concept.concept_name, concept.rerank_score)

# Chat with an agent
reply = kweaver.chat("Analyse the inventory risks for this year")
print(reply.content)

# Streaming output
for chunk in kweaver.chat("Generate a risk report", stream=True):
    print(chunk.delta, end="", flush=True)
```

---

### Scenario 2: Write data then rebuild the index

After connecting new datasources or adding object/relation types, call `weaver()` to rebuild the BKN index so changes become searchable by agents.

```python
import kweaver
from kweaver import KWeaverClient, TokenAuth

kweaver.configure(
    url="https://kweaver.example.com",
    token="my-token",
    bkn_id="supply-chain-bkn-id",
)

# Use the low-level client for write operations
client = kweaver._default_client
client.datasources.create(name="erp_db", type="mysql", ...)
client.object_types.create(bkn_id="supply-chain-bkn-id", ...)

# Trigger a full BKN build after writes (default timeout: 300s)
kweaver.weaver(wait=True)
print("BKN build complete — ready to search")

# Now search the newly indexed data
results = kweaver.search("Which suppliers are in the newly imported ERP data?")
```

Async (non-blocking) build:

```python
job = kweaver.weaver()          # Returns a BuildJob immediately
status = job.poll()             # Poll manually
print(status.state)             # "running" / "completed" / "failed"

# Or wait later
status = job.wait(timeout=600)
```

---

### Scenario 3: Manage multiple BKNs

When operating on multiple BKNs simultaneously, pass `bkn_id` explicitly to each call:

```python
import kweaver

kweaver.configure(
    url="https://kweaver.example.com",
    token="my-token",
)

# List all BKNs
for bkn in kweaver.bkns():
    print(bkn.id, bkn.name)

# Search different BKNs
results_sc = kweaver.search("inventory alert", bkn_id="supply-chain-bkn-id")
results_hr = kweaver.search("employee turnover", bkn_id="hr-bkn-id")

# Rebuild specific BKNs
kweaver.weaver(bkn_id="supply-chain-bkn-id", wait=True)
kweaver.weaver(bkn_id="hr-bkn-id", wait=True)
```

---

### Scenario 4: Browse agents

```python
import kweaver

kweaver.configure(url="https://kweaver.example.com", token="my-token")

# List all published agents
for agent in kweaver.agents(status="published"):
    print(f"{agent.name}  (id={agent.id}, bkn={agent.kn_ids})")

# Multi-turn conversation with a specific agent
conv_id = ""
for question in ["What can you do?", "Analyse recent inventory data", "Give improvement suggestions"]:
    reply = kweaver.chat(question, agent_id="supply-chain-agent-id", conversation_id=conv_id)
    conv_id = reply.conversation_id
    print(f"Q: {question}")
    print(f"A: {reply.content}\n")
```

---

## API Reference

### `kweaver.configure(url, *, token, bkn_id, agent_id, ...)`

Initialises the default client. Must be called before any other function.

| Parameter | Description |
|---|---|
| `url` | KWeaver service URL |
| `token` | Bearer token (recommended) |
| `username` / `password` | Username/password login (requires Playwright) |
| `config` | Load credentials from the local config file (`~/.kweaver/`) |
| `bkn_id` | Default BKN ID used by `search()` and `weaver()` |
| `agent_id` | Default Agent ID used by `chat()` |

### `kweaver.search(query, *, bkn_id, mode, max_concepts)`

Semantic search over a BKN. Returns `SemanticSearchResult`.

### `kweaver.chat(message, *, agent_id, stream, conversation_id)`

Send a message to an agent. Returns `Message` (or `Iterator[MessageChunk]` when `stream=True`).

### `kweaver.weaver(*, bkn_id, wait, timeout)`

Trigger a full BKN build / index rebuild. **Only needed after write operations** — read-only use cases do not require this. Returns `BuildJob`.

### `kweaver.agents(*, keyword, status, limit)`

List agents. Returns `list[Agent]`.

### `kweaver.bkns(*, name, limit)`

List BKNs. Returns `list[KnowledgeNetwork]`.

---

## Low-level Client

The top-level API covers the most common operations. For full access (datasources, object types, relation types, actions, etc.), use the low-level client directly:

```python
import kweaver

kweaver.configure(url="...", token="...")
client = kweaver._default_client   # KWeaverClient instance

# Full API
client.datasources.list(bkn_id="...")
client.object_types.list(bkn_id="...")
client.action_types.execute(bkn_id="...", action_type_id="...")
```

Or instantiate directly:

```python
from kweaver import KWeaverClient, TokenAuth

client = KWeaverClient(
    base_url="https://kweaver.example.com",
    auth=TokenAuth("my-token"),
)
```

## Links

- [GitHub](https://github.com/kweaver-ai/kweaver-sdk)
- [TypeScript SDK on npm](https://www.npmjs.com/package/@kweaver-ai/kweaver-sdk)

## License

MIT
