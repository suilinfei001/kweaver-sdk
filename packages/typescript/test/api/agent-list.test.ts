import test from "node:test";
import assert from "node:assert/strict";
import {
  listAgents,
  getAgent,
  getAgentByKey,
  createAgent,
  updateAgent,
  deleteAgent,
  publishAgent,
  unpublishAgent,
} from "../../src/api/agent-list.js";

const originalFetch = globalThis.fetch;

function mockFetchResponse(data: unknown, status = 200): ReturnType<typeof fetch> {
  return async () =>
    new Response(JSON.stringify(data), {
      status,
      headers: { "content-type": "application/json" },
    });
}

test("listAgents returns entries on 200", async () => {
  const payload = { entries: [{ id: "a1", name: "Test" }] };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await listAgents({
    baseUrl: "https://test.com",
    accessToken: "token",
  });

  assert.equal(JSON.parse(result).entries[0].id, "a1");
  globalThis.fetch = originalFetch;
});

test("listAgents with filters sends correct params", async () => {
  globalThis.fetch = async (url: string, init?: RequestInit) => {
    const body = init?.body as string;
    assert.ok(body);
    const parsed = JSON.parse(body);
    assert.equal(parsed.name, "test");
    assert.equal(parsed.limit, 10);
    return mockFetchResponse({ entries: [] })();
  };

  await listAgents({
    baseUrl: "https://test.com",
    accessToken: "token",
    name: "test",
    limit: 10,
  });

  globalThis.fetch = originalFetch;
});

test("getAgent returns agent on 200", async () => {
  const payload = { id: "a1", name: "Agent1", config: {} };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await getAgent({
    baseUrl: "https://test.com",
    accessToken: "token",
    agentId: "a1",
  });

  assert.equal(JSON.parse(result).id, "a1");
  globalThis.fetch = originalFetch;
});

test("getAgentByKey returns agent on 200", async () => {
  const payload = { id: "a1", key: "test-key", name: "Agent1" };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await getAgentByKey({
    baseUrl: "https://test.com",
    accessToken: "token",
    key: "test-key",
  });

  assert.equal(JSON.parse(result).key, "test-key");
  globalThis.fetch = originalFetch;
});

test("createAgent returns created agent on 200", async () => {
  const payload = { id: "a1", name: "NewAgent" };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await createAgent({
    baseUrl: "https://test.com",
    accessToken: "token",
    body: JSON.stringify({ name: "NewAgent" }),
  });

  assert.equal(JSON.parse(result).id, "a1");
  globalThis.fetch = originalFetch;
});

test("updateAgent returns updated agent on 200", async () => {
  const payload = { id: "a1", name: "UpdatedAgent" };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await updateAgent({
    baseUrl: "https://test.com",
    accessToken: "token",
    agentId: "a1",
    body: JSON.stringify({ name: "UpdatedAgent" }),
  });

  assert.equal(JSON.parse(result).id, "a1");
  globalThis.fetch = originalFetch;
});

test("deleteAgent succeeds on 200", async () => {
  globalThis.fetch = async () =>
    new Response(null, {
      status: 200,
      headers: { "content-type": "application/json" },
    });

  await deleteAgent({
    baseUrl: "https://test.com",
    accessToken: "token",
    agentId: "a1",
  });

  globalThis.fetch = originalFetch;
});

test("publishAgent returns result on 200", async () => {
  const payload = { success: true };
  globalThis.fetch = mockFetchResponse(payload);

  const result = await publishAgent({
    baseUrl: "https://test.com",
    accessToken: "token",
    agentId: "a1",
  });

  assert.equal(JSON.parse(result).success, true);
  globalThis.fetch = originalFetch;
});

test("unpublishAgent succeeds on 200", async () => {
  globalThis.fetch = async () =>
    new Response(null, {
      status: 200,
      headers: { "content-type": "application/json" },
    });

  await unpublishAgent({
    baseUrl: "https://test.com",
    accessToken: "token",
    agentId: "a1",
  });

  globalThis.fetch = originalFetch;
});
