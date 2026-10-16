import { NextRequest } from "next/server";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyRequest(request: NextRequest, context: RouteContext) {
  const apiBaseUrl = process.env.GMS_API_BASE_URL?.replace(/\/$/, "");

  if (!apiBaseUrl) {
    return Response.json(
      { detail: "GMS_API_BASE_URL is not configured." },
      { status: 503 }
    );
  }

  const path = (await context.params).path
    .map((segment) => encodeURIComponent(segment))
    .join("/");
  const upstreamUrl = new URL(`${apiBaseUrl}/${path}`);

  request.nextUrl.searchParams.forEach((value, key) => {
    upstreamUrl.searchParams.append(key, value);
  });

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");
  headers.delete("accept-encoding");

  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 512 * 1024) {
        await reader.cancel();
        return Response.json({detail: "Request body is too large."}, {status: 413});
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    if (size) body = bytes.buffer;
  }

  if (!body) {
    headers.delete("content-type");
  }

  let upstreamResponse: Response;
  try {
    upstreamResponse = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual"
    });
  } catch {
    return Response.json(
      { detail: "GMS service is temporarily unavailable." },
      { status: 503 }
    );
  }

  const responseHeaders = new Headers(upstreamResponse.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  responseHeaders.delete("transfer-encoding");

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: responseHeaders
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
