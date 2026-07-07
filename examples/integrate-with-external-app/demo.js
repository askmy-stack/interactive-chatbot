/**
 * Minimal Node.js integration demo.
 * Run: node demo.js (with API at localhost:8000)
 */

const BASE = process.env.ASK_BASE_URL || "http://localhost:8000";

async function ask(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-ASK-Client": "external-app",
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function main() {
  const health = await ask("/health");
  console.log(`A.S.K. status: ${health.status} (provider: ${health.provider})`);

  const reply = await ask("/chat", {
    method: "POST",
    body: JSON.stringify({
      message: "What can you help me with?",
      session_id: "demo",
      input_channel: "text",
      output_channel: "text",
    }),
  });
  console.log(`Response: ${reply.response}`);

  const brief = await ask("/brief/morning");
  console.log(`Morning brief:\n${brief.brief}`);
}

main().catch(console.error);
