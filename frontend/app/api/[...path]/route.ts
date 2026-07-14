import { NextRequest, NextResponse } from "next/server";

import { buildDownstreamResponseHeaders, buildProxyTargetUrl, buildUpstreamRequestHeaders } from "@/lib/ask-proxy";

export const dynamic = "force-dynamic";

async function proxy(req: NextRequest, path: string[]): Promise<NextResponse> {
  const target = buildProxyTargetUrl(process.env, path, req.nextUrl.search);
  const hasBody = !["GET", "HEAD"].includes(req.method);

  const upstream = await fetch(target, {
    method: req.method,
    headers: buildUpstreamRequestHeaders(req.headers, process.env),
    body: hasBody ? await req.arrayBuffer() : undefined,
    // @ts-expect-error - undici-only option required for streaming request bodies
    duplex: hasBody ? "half" : undefined,
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: buildDownstreamResponseHeaders(upstream.headers),
  });
}

type RouteParams = { params: Promise<{ path: string[] }> };

export async function GET(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}

export async function POST(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}

export async function PUT(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}

export async function DELETE(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}

export async function PATCH(req: NextRequest, { params }: RouteParams) {
  return proxy(req, (await params).path);
}
