// Run inside the final frontend image, with this file mounted read-only.
const assert = require("node:assert/strict");
const http = require("node:http");
const {execFileSync} = require("node:child_process");

async function main() {
  assert.notEqual(process.getuid(), 0);
  assert.match(execFileSync("getcap", ["/usr/local/bin/node"], {encoding: "utf8"}), /cap_net_bind_service=ep/);
  process.env.GMS_API_BASE_URL = "http://127.0.0.1:8000";
  let calls = 0;
  const upstream = http.createServer((request, response) => {
    calls++;
    if (request.url === "/redirect") {
      response.writeHead(307, {Location: "https://example.invalid/no-follow"});
      response.end();
      return;
    }
    let body = "";
    request.on("data", chunk => body += chunk);
    request.on("end", () => {
      response.writeHead(200, {"Content-Type": "application/json", "Cache-Control": "no-store"});
      response.end(JSON.stringify({url: request.url, method: request.method,
        authorization: request.headers.authorization, app: request.headers["x-app-id"],
        key: request.headers["x-api-key"], body}));
    });
  });
  await new Promise(resolve => upstream.listen(8000, "127.0.0.1", resolve));
  require("/app/server.js");
  const base = "http://127.0.0.1:80";
  for (let i = 0; i < 100; i++) {
    try { if ((await fetch(base + "/login")).ok) break; } catch {}
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  for (const route of ["/login", "/setup-password", "/apps", "/policies", "/settings", "/policy-preview"]) {
    const response = await fetch(base + route);
    assert.equal(response.status, 200, route);
    assert.match(await response.text(), /<!DOCTYPE html>/i);
  }
  const response = await fetch(base + "/api/gms/echo/branch%20name?q=a%20b", {
    method: "POST", headers: {Authorization: "Bearer fake-review-token", "X-App-ID": "fake-app",
      "X-API-Key": "fake-review-key", "Content-Type": "application/json"}, body: '{"message":"fake payload"}'
  });
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.url, "/echo/branch%20name?q=a+b");
  assert.equal(result.authorization, "Bearer fake-review-token");
  assert.equal(result.app, "fake-app");
  assert.equal(result.key, "fake-review-key");
  assert.equal(result.body, '{"message":"fake payload"}');
  const before = calls;
  const oversized = await fetch(base + "/api/gms/echo", {method: "POST", body: "x".repeat(512 * 1024 + 1)});
  assert.equal(oversized.status, 413);
  assert.equal(calls, before);
  const redirect = await fetch(base + "/api/gms/redirect", {redirect: "manual"});
  assert.equal(redirect.status, 307);
  assert.equal(redirect.headers.get("location"), "https://example.invalid/no-follow");
  console.log("Frontend image checks passed: non-root port 80/capability, six pages, encoded async routes, credential forwarding, body limit and manual redirects.");
}

main().then(() => process.exit(0)).catch(error => { console.error(error); process.exit(1); });
