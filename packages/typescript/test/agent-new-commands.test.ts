import test from "node:test";
import assert from "node:assert/strict";
import {
  formatSimpleAgentList,
  parseAgentListArgs,
  parseAgentGetArgs,
  parseAgentSessionsArgs,
  parseAgentHistoryArgs,
  parseAgentTraceArgs,
} from "../src/commands/agent.js";

test("formatSimpleAgentList with entries", () => {
  const input = JSON.stringify({
    entries: [
      { id: "a1", name: "Agent1", description: "Test agent 1" },
      { id: "a2", name: "Agent2", description: "Test agent 2" },
    ],
  });

  const result = formatSimpleAgentList(input, true);
  const parsed = JSON.parse(result);

  assert.equal(parsed.length, 2);
  assert.equal(parsed[0].id, "a1");
  assert.equal(parsed[0].name, "Agent1");
  assert.equal(parsed[0].description, "Test agent 1");
  assert.equal(parsed[1].id, "a2");
  assert.equal(parsed[1].name, "Agent2");
  assert.equal(parsed[1].description, "Test agent 2");
});

test("formatSimpleAgentList with alternative field names", () => {
  const input = JSON.stringify({
    entries: [
      { agent_id: "a1", agent_name: "Agent1", comment: "Test agent 1" },
    ],
  });

  const result = formatSimpleAgentList(input, true);
  const parsed = JSON.parse(result);

  assert.equal(parsed.length, 1);
  assert.equal(parsed[0].id, "a1");
  assert.equal(parsed[0].name, "Agent1");
  assert.equal(parsed[0].description, "Test agent 1");
});

test("formatSimpleAgentList with array input", () => {
  const input = JSON.stringify([
    { id: "a1", name: "Agent1", description: "Test agent 1" },
    { id: "a2", name: "Agent2", description: "Test agent 2" },
  ]);

  const result = formatSimpleAgentList(input, true);
  const parsed = JSON.parse(result);

  assert.equal(parsed.length, 2);
  assert.equal(parsed[0].id, "a1");
  assert.equal(parsed[1].id, "a2");
});

test("formatSimpleAgentList handles missing fields gracefully", () => {
  const input = JSON.stringify({
    entries: [
      { id: "a1" }, // Missing name and description
    ],
  });

  const result = formatSimpleAgentList(input, true);
  const parsed = JSON.parse(result);

  assert.equal(parsed.length, 1);
  assert.equal(parsed[0].id, "a1");
  assert.equal(parsed[0].name, "");
  assert.equal(parsed[0].description, "");
});

test("parseAgentListArgs with defaults", () => {
  const result = parseAgentListArgs([]);

  assert.equal(result.name, "");
  assert.equal(result.offset, 0);
  assert.equal(result.limit, 30);
  assert.equal(result.category_id, "");
  assert.equal(result.custom_space_id, "");
  assert.equal(result.is_to_square, 1);
  assert.equal(result.pretty, true);
  assert.equal(result.verbose, false);
});

test("parseAgentListArgs with name filter", () => {
  const result = parseAgentListArgs(["--name", "test"]);

  assert.equal(result.name, "test");
  assert.equal(result.limit, 30);
});

test("parseAgentListArgs with offset and limit", () => {
  const result = parseAgentListArgs(["--offset", "10", "--limit", "50"]);

  assert.equal(result.offset, 10);
  assert.equal(result.limit, 50);
});

test("parseAgentListArgs with category and custom space", () => {
  const result = parseAgentListArgs([
    "--category-id",
    "cat1",
    "--custom-space-id",
    "space1",
  ]);

  assert.equal(result.category_id, "cat1");
  assert.equal(result.custom_space_id, "space1");
});

test("parseAgentListArgs with is_to_square", () => {
  const result = parseAgentListArgs(["--is-to-square", "0"]);

  assert.equal(result.is_to_square, 0);
});

test("parseAgentListArgs with verbose flag", () => {
  const result = parseAgentListArgs(["--verbose"]);

  assert.equal(result.verbose, true);
});

test("parseAgentListArgs with business domain", () => {
  const result = parseAgentListArgs(["-bd", "bd_test"]);

  assert.equal(result.businessDomain, "bd_test");
});

test("parseAgentListArgs with invalid offset defaults to 0", () => {
  const result = parseAgentListArgs(["--offset", "invalid"]);

  assert.equal(result.offset, 0);
});

test("parseAgentListArgs with invalid limit defaults to 30", () => {
  const result = parseAgentListArgs(["--limit", "invalid"]);

  assert.equal(result.limit, 30);
});

test("parseAgentListArgs throws on unsupported argument", () => {
  assert.throws(
    () => parseAgentListArgs(["--unsupported"]),
    (error: Error) => error.message.includes("Unsupported agent list argument")
  );
});

test("parseAgentGetArgs with agent ID", () => {
  const result = parseAgentGetArgs(["a1"]);

  assert.equal(result.agentId, "a1");
  assert.equal(result.pretty, true);
  assert.equal(result.verbose, false);
});

test("parseAgentGetArgs with business domain", () => {
  const result = parseAgentGetArgs(["a1", "-bd", "bd_test"]);

  assert.equal(result.agentId, "a1");
  assert.equal(result.businessDomain, "bd_test");
});

test("parseAgentGetArgs with verbose flag", () => {
  const result = parseAgentGetArgs(["a1", "--verbose"]);

  assert.equal(result.agentId, "a1");
  assert.equal(result.verbose, true);
});

test("parseAgentGetArgs throws on missing agent ID", () => {
  assert.throws(
    () => parseAgentGetArgs([]),
    (error: Error) => error.message.includes("Missing agent_id")
  );
});

test("parseAgentGetArgs throws on unsupported argument", () => {
  assert.throws(
    () => parseAgentGetArgs(["a1", "--unsupported"]),
    (error: Error) => error.message.includes("Unsupported agent get argument")
  );
});

test("parseAgentSessionsArgs with agent ID", () => {
  const result = parseAgentSessionsArgs(["a1"]);

  assert.equal(result.agentId, "a1");
  assert.equal(result.limit, 30);
  assert.equal(result.pretty, true);
});

test("parseAgentSessionsArgs with limit", () => {
  const result = parseAgentSessionsArgs(["a1", "--limit", "50"]);

  assert.equal(result.agentId, "a1");
  assert.equal(result.limit, 50);
});

test("parseAgentSessionsArgs with business domain", () => {
  const result = parseAgentSessionsArgs(["a1", "-bd", "bd_test"]);

  assert.equal(result.agentId, "a1");
  assert.equal(result.businessDomain, "bd_test");
});

test("parseAgentSessionsArgs throws on missing agent ID", () => {
  assert.throws(
    () => parseAgentSessionsArgs([]),
    (error: Error) => error.message.includes("Missing agent_id")
  );
});

test("parseAgentHistoryArgs with conversation ID", () => {
  const result = parseAgentHistoryArgs(["conv1"]);

  assert.equal(result.conversationId, "conv1");
  assert.equal(result.limit, 30);
  assert.equal(result.pretty, true);
});

test("parseAgentHistoryArgs with limit", () => {
  const result = parseAgentHistoryArgs(["conv1", "--limit", "50"]);

  assert.equal(result.conversationId, "conv1");
  assert.equal(result.limit, 50);
});

test("parseAgentHistoryArgs with business domain", () => {
  const result = parseAgentHistoryArgs(["conv1", "-bd", "bd_test"]);

  assert.equal(result.conversationId, "conv1");
  assert.equal(result.businessDomain, "bd_test");
});

test("parseAgentHistoryArgs throws on missing conversation ID", () => {
  assert.throws(
    () => parseAgentHistoryArgs([]),
    (error: Error) => error.message.includes("Missing conversation_id")
  );
});

test("parseAgentTraceArgs with conversation ID", () => {
  const result = parseAgentTraceArgs(["conv1"]);

  assert.equal(result.conversationId, "conv1");
  assert.equal(result.pretty, true);
});

test("parseAgentTraceArgs with compact flag", () => {
  const result = parseAgentTraceArgs(["conv1", "--compact"]);

  assert.equal(result.conversationId, "conv1");
  assert.equal(result.pretty, false);
});

test("parseAgentTraceArgs throws on missing conversation ID", () => {
  assert.throws(
    () => parseAgentTraceArgs([]),
    (error: Error) => error.message.includes("Missing conversation_id")
  );
});
