// Test transport boundary only. Source modules and CLI arguments remain unchanged.
import { appendFileSync } from "node:fs";
const realFetch = globalThis.fetch;
const origin = process.env.ORACLE_HTTP_ORIGIN;
globalThis.fetch = async (input, options) => {
  const url = new URL(typeof input === "string" || input instanceof URL ? input : input.url);
  // Ink's Yoga uses an inline WASM data URL; it does not reach a network.
  const allowed = url.protocol === "data:" || url.origin === origin;
  appendFileSync(process.env.ORACLE_NETWORK_LOG, JSON.stringify({
    method: options?.method ?? "GET", url: url.protocol === "data:" ? "data:[inline resource]" : url.href, allowed,
  }) + "\n");
  if (!allowed) throw new Error("Oracle transport blocked non-fixture fetch");
  return realFetch(input, options);
};
