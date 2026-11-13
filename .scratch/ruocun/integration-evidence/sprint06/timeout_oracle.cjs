// Node22 built-in semantics used at frozen src/client/client.ts:150, before fetch.
for (const raw of ["-1", "Infinity", "-Infinity", "NaN", "0.1", "4294967295", "4294967296", "9007199254740991", "9007199254740992", "1", "2147483648"]) {
  try {
    const signal = AbortSignal.timeout(Number(raw));
    console.log(JSON.stringify({ raw, created: true, aborted: signal.aborted }));
  } catch (e) {
    console.log(JSON.stringify({ raw, created: false, code: e.code, name: e.name }));
  }
}
