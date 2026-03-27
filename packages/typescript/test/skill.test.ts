import test from "node:test";
import assert from "node:assert/strict";

import { KWeaverClient } from "../src/client.js";
import { parseSkillListArgs, parseSkillRegisterArgs } from "../src/commands/skill.js";

const BASE = "https://mock.kweaver.test";
const TOKEN = "test-token-abc";

test("parseSkillListArgs uses list default page size 30", () => {
  const parsed = parseSkillListArgs(["--name", "demo"]);
  assert.equal(parsed.page, 1);
  assert.equal(parsed.pageSize, 30);
  assert.equal(parsed.name, "demo");
});

test("parseSkillRegisterArgs requires exactly one source flag", () => {
  assert.throws(() => parseSkillRegisterArgs([]), /exactly one/);
  assert.throws(
    () => parseSkillRegisterArgs(["--content-file", "a.md", "--zip-file", "a.zip"]),
    /exactly one/
  );
});

test("client.skills.list unwraps envelope data", async () => {
  const orig = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(
      JSON.stringify({
        code: 0,
        data: { total_count: 1, page: 1, page_size: 30, data: [{ skill_id: "skill-1", name: "demo" }] },
      }),
      { status: 200 }
    );

  try {
    const client = new KWeaverClient({ baseUrl: BASE, accessToken: TOKEN });
    const result = await client.skills.list();
    assert.equal(result.data.length, 1);
    assert.equal(result.data[0]?.skill_id, "skill-1");
  } finally {
    globalThis.fetch = orig;
  }
});

test("client.skills.fetchContent resolves index then fetches remote markdown", async () => {
  const orig = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async (input) => {
    calls += 1;
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/content")) {
      return new Response(
        JSON.stringify({
          code: 0,
          data: {
            skill_id: "skill-1",
            url: "https://download.example/SKILL.md",
            files: [{ rel_path: "refs/guide.md" }],
          },
        }),
        { status: 200 }
      );
    }
    return new Response("# Demo skill\n", { status: 200 });
  };

  try {
    const client = new KWeaverClient({ baseUrl: BASE, accessToken: TOKEN });
    const content = await client.skills.fetchContent("skill-1");
    assert.equal(content, "# Demo skill\n");
    assert.equal(calls, 2);
  } finally {
    globalThis.fetch = orig;
  }
});
