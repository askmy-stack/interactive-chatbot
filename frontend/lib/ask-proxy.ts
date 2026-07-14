/**
 * Server-side proxy helpers for forwarding browser requests to the A.S.K. API.
 *
 * Kept separate from the route handler so the header/URL logic (the part that
 * matters for the "don't leak the API key to the browser" guarantee) can be
 * unit tested without needing a running Next.js server.
 */

const HOP_BY_HOP_REQUEST_HEADERS = new Set(["host", "connection", "content-length"]);
const HOP_BY_HOP_RESPONSE_HEADERS = new Set(["content-encoding", "content-length", "transfer-encoding", "connection"]);

export interface AskProxyEnv {
  ASK_API_URL?: string;
  ASK_API_KEY?: string;
  [key: string]: string | undefined;
}

export function resolveAskApiUrl(env: AskProxyEnv): string {
  return (env.ASK_API_URL || "http://localhost:8000").replace(/\/+$/, "");
}

export function buildProxyTargetUrl(env: AskProxyEnv, path: string[], search: string): string {
  const base = resolveAskApiUrl(env);
  const suffix = path.map(encodeURIComponent).join("/");
  return `${base}/${suffix}${search}`;
}

/**
 * Build outbound request headers for the upstream A.S.K. API call.
 *
 * The API key is injected here, server-side, from `ASK_API_KEY` (never
 * `NEXT_PUBLIC_*`) — the browser never sees it.
 */
export function buildUpstreamRequestHeaders(incoming: Headers, env: AskProxyEnv): Headers {
  const headers = new Headers();
  incoming.forEach((value, key) => {
    if (!HOP_BY_HOP_REQUEST_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  headers.set("X-ASK-Client", "standalone-web");
  if (env.ASK_API_KEY) {
    headers.set("Authorization", `Bearer ${env.ASK_API_KEY}`);
  } else {
    headers.delete("authorization");
  }
  return headers;
}

export function buildDownstreamResponseHeaders(upstream: Headers): Headers {
  const headers = new Headers();
  upstream.forEach((value, key) => {
    if (!HOP_BY_HOP_RESPONSE_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}
