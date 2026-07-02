"use client";

import { useState } from "react";
import { Eye, EyeOff, Play } from "lucide-react";
import { runGuardrails, type GuardrailsRunResponse } from "@/lib/api-client";

export function AppRuntimeTest({ clientId }: { clientId: string }) {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [conversationId, setConversationId] = useState("frontend-demo-1");
  const [message, setMessage] = useState("List recent pull requests.");
  const [result, setResult] = useState<GuardrailsRunResponse | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function handleRun() {
    if (!apiKey || !message.trim()) {
      return;
    }
    setRunning(true);
    setError("");
    setResult(null);
    try {
      setResult(
        await runGuardrails(clientId, apiKey, {
          message: message.trim(),
          conversation_id: conversationId.trim() || null,
          conversation_history: []
        })
      );
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "Runtime request failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-extrabold text-gms-text">Runtime Test</h2>
      <p className="mt-2 text-sm text-gms-muted">
        Send a real authenticated request through input rails, guarded tools and output rails.
      </p>
      <div className="mt-7 grid gap-5 md:grid-cols-2">
        <label className="text-sm font-bold text-gms-text">
          App API Key
          <div className="relative mt-2">
            <input
              className="detail-input pr-12"
              placeholder="Enter the app API key"
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
            />
            <button
              className="absolute right-3 top-3 text-gms-muted"
              type="button"
              onClick={() => setShowKey((current) => !current)}
            >
              {showKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </label>
        <label className="text-sm font-bold text-gms-text">
          Conversation ID
          <input
            className="detail-input mt-2"
            value={conversationId}
            onChange={(event) => setConversationId(event.target.value)}
          />
        </label>
      </div>
      <label className="mt-5 block text-sm font-bold text-gms-text">
        Message
        <textarea
          className="mt-2 h-32 w-full resize-none rounded-md border border-gms-line bg-white p-4 text-sm text-gms-text outline-none focus:border-gms-blue dark:bg-[#252932]"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
      </label>
      <button
        className="mt-5 inline-flex h-10 items-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button disabled:opacity-50"
        disabled={!apiKey || !message.trim() || running}
        type="button"
        onClick={handleRun}
      >
        <Play className="h-4 w-4" />
        {running ? "Running..." : "Run Guardrails"}
      </button>

      {result && (
        <div className="mt-7 rounded-md border border-gms-line bg-[#f9fbff] p-5 dark:bg-[#20242c]">
          <div className="flex flex-wrap gap-2">
            <Status label={`Status: ${result.status}`} passed={result.status === "passed"} />
            <Status label={`Input: ${formatRailStatus(result.input_rail_status, result.input_rail_source, result.input_rail_categories)}`} passed={result.input_rail_status === "passed"} />
            <Status label={`Tool guard: ${formatToolGuardStatus(result)}`} passed={result.tool_guard_status === "passed"} />
            <Status label={`Output: ${formatRailStatus(result.output_rail_status, result.output_rail_source, result.output_rail_categories)}`} passed={result.output_rail_status === "passed"} />
          </div>
          <h3 className="mt-5 text-sm font-bold text-gms-text">Response</h3>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-gms-text">{result.response}</p>
          <dl className="mt-5 grid gap-3 text-xs text-gms-muted md:grid-cols-4">
            <div><dt>Input policies</dt><dd className="mt-1 text-lg font-bold text-gms-text">{result.input_policy_count}</dd></div>
            <div><dt>Output policies</dt><dd className="mt-1 text-lg font-bold text-gms-text">{result.output_rule_count}</dd></div>
            <div><dt>Guarded tool types</dt><dd className="mt-1 text-lg font-bold text-gms-text">{result.blocked_tools.length}</dd></div>
            <div><dt>History used</dt><dd className="mt-1 text-lg font-bold text-gms-text">{result.history_messages_used}</dd></div>
          </dl>
        </div>
      )}
      {error && <p className="mt-4 text-sm text-gms-danger">{error}</p>}
    </div>
  );
}

function formatToolGuardStatus(result: GuardrailsRunResponse) {
  if (result.tool_guard_status === "blocked") return "blocked (GMS)";
  return result.tool_guard_status;
}

function formatRailStatus(
  railStatus: string | null,
  source: string | null,
  categories: string[],
) {
  const status = railStatus ?? "not run";
  if (status !== "blocked") return status;

  if (source?.startsWith("azure")) {
    const categoryLabel = categories.join(", ");
    return categoryLabel ? `blocked (Azure: ${categoryLabel})` : "blocked (Azure)";
  }

  return "blocked (GMS)";
}

function Status({ label, passed }: { label: string; passed: boolean }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${passed ? "bg-[#e7f7ed] text-[#257342]" : "bg-[#fff0f1] text-gms-danger"}`}>
      {label}
    </span>
  );
}
