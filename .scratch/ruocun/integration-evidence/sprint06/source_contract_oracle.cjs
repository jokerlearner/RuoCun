// Run unmodified frozen source modules, transpiling syntax only into a private cache.
const fs = require("node:fs");
const path = require("node:path");
const ts = require(process.argv[2]);
const cache = path.resolve(".cache/sprint06-source");
for (const name of ["client/client", "client/responses", "client/sse", "config/profiles"]) {
  const input = path.join(cache, "src", name + ".ts");
  const result = ts.transpileModule(fs.readFileSync(input, "utf8"), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
  });
  fs.writeFileSync(path.join(cache, "src", name + ".js"), result.outputText);
}
const { streamChat } = require(path.join(cache, "src/client/client.js"));
const encoder = new TextEncoder();
const sse = (payload) => encoder.encode("data: " + JSON.stringify(payload) + "\n\n");
const success = () => new Response(sse({ choices: [{ delta: { content: "recovered" } }] }));
async function run(label, fetchImpl, extra = {}) {
  const iterator = streamChat({ baseUrl: "http://127.0.0.1:1", apiKey: "synthetic", model: "synthetic",
    messages: [], maxRetries: 1, retryDelayMs: 0, fetchImpl, ...extra });
  const deltas = [];
  try {
    while (true) {
      const result = await iterator.next();
      if (result.done) { console.log(JSON.stringify({ label, deltas, message: result.value })); break; }
      deltas.push(result.value);
    }
  } catch (e) { console.log(JSON.stringify({ label, deltas, error: e.message, status: e.status ?? null })); }
}
(async () => {
  let fallbackCalls = 0;
  await run("fallback-json-error-after-429", async () => {
    fallbackCalls++;
    return fallbackCalls === 1
      ? new Response("", { status: 429, headers: { "retry-after": "0" } })
      : new Response("synthetic-invalid-json");
  }, { maxRetries: 0 });
  console.log(JSON.stringify({ label: "fallback-json-error-after-429", calls: fallbackCalls }));
  for (const header of [" ", "0x0", "0b0", "abc"]) {
    let calls = 0;
    await run("retry-after:" + JSON.stringify(header), async () => {
      calls++;
      return calls === 1 ? new Response("", { status: 429, headers: { "retry-after": header } }) : success();
    });
    console.log(JSON.stringify({ header, calls }));
  }
  for (const frag of [{ index: 0, id: "synthetic-call" }, { index: 0, function: { arguments: "{" } },
    { index: 0, function: { name: "Read" } }]) {
    let calls = 0;
    await run("fragment:" + JSON.stringify(frag), async () => {
      calls++;
      if (calls > 1) return success();
      let pulled = false;
      return new Response(new ReadableStream({ pull(controller) {
        if (!pulled) { pulled = true; controller.enqueue(sse({ choices: [{ delta: { tool_calls: [frag] } }] })); }
        else controller.error(new Error("socket closed unexpectedly"));
      } }));
    });
    console.log(JSON.stringify({ fragment: frag, calls }));
  }
})();
