import { NextResponse } from "next/server";

const rawApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const apiBaseUrl = rawApiBaseUrl.replace(/\/$/, "");

type RuntimeProxyBody = {
  client_id?: string;
  message?: string;
  conversation_id?: string | null;
  conversation_history?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
};

function apiKeyForClient(clientId: string) {
  const keyedConfig = process.env.GMS_DEMO_RUNTIME_API_KEYS ?? "";
  const entries = keyedConfig
    .split(";")
    .map((entry) => entry.trim())
    .filter(Boolean);

  for (const entry of entries) {
    const separatorIndex = entry.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }
    const keyClientId = entry.slice(0, separatorIndex).trim();
    const keyValue = entry.slice(separatorIndex + 1).trim();
    if (keyClientId === clientId && keyValue) {
      return keyValue;
    }
  }

  return process.env.GMS_DEMO_RUNTIME_API_KEY ?? "";
}

export async function POST(request: Request) {
  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "NEXT_PUBLIC_API_BASE_URL is not configured." },
      { status: 500 }
    );
  }

  const body = (await request.json().catch(() => null)) as RuntimeProxyBody | null;
  const clientId = body?.client_id?.trim();
  const message = body?.message?.trim();

  if (!clientId || !message) {
    return NextResponse.json(
      { detail: "client_id and message are required." },
      { status: 400 }
    );
  }

  const apiKey = apiKeyForClient(clientId);
  if (!apiKey) {
    return NextResponse.json(
      {
        detail:
          "Runtime test API key is not configured for this app. Set GMS_DEMO_RUNTIME_API_KEY or GMS_DEMO_RUNTIME_API_KEYS in frontend/.env.local."
      },
      { status: 400 }
    );
  }

  const runtimeResponse = await fetch(`${apiBaseUrl}/v1/guardrails/run`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-App-ID": clientId,
      "X-API-Key": apiKey
    },
    body: JSON.stringify({
      message,
      conversation_id: body?.conversation_id ?? null,
      conversation_history: body?.conversation_history ?? []
    }),
    cache: "no-store"
  });

  const responseText = await runtimeResponse.text();
  return new NextResponse(responseText, {
    status: runtimeResponse.status,
    headers: {
      "Content-Type":
        runtimeResponse.headers.get("Content-Type") ?? "application/json"
    }
  });
}
