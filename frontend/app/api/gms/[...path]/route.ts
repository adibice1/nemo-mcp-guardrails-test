import { NextRequest } from "next/server";

type RouteContext = {
  params: { path: string[] };
};

async function proxyRequest(request: NextRequest, context: RouteContext) {
  const apiBaseUrl = process.env.GMS_API_BASE_URL?.replace(/\/$/, "");

  if (!apiBaseUrl) {
    return Response.json(
      { detail: "GMS_API_BASE_URL is not configured." },
      { status: 503 }
    );
  }

  const path = context.params.path
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

  const bodyBuffer =
    request.method === "GET" || request.method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  const body =
    bodyBuffer && bodyBuffer.byteLength > 0 ? bodyBuffer : undefined;

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
