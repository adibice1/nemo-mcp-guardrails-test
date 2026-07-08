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
        The API key field is only for this local GMS test panel; real apps send it from their backend.
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
          <RuntimeProgress result={result} />
          <h3 className="mt-5 text-sm font-bold text-gms-text">Response</h3>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-gms-text">{result.response}</p>
          {result.debug_tool_trace && result.debug_tool_trace.length > 0 && (
            <div className="mt-5 rounded-md border border-gms-line bg-white p-4 text-xs text-gms-text dark:bg-[#252932]">
              <h3 className="text-sm font-extrabold">Connector debug trace</h3>
              <div className="mt-3 space-y-3">
                {result.debug_tool_trace.map((entry, index) => (
                  <div key={`${entry.event}-${entry.tool_name ?? "tool"}-${index}`}>
                    <p className="font-bold">
                      {entry.event}
                      {entry.tool_name ? `: ${entry.tool_name}` : ""}
                    </p>
                    {entry.arguments && (
                      <pre className="mt-1 whitespace-pre-wrap rounded bg-[#f4f7ff] p-2 dark:bg-[#1b1f27]">
                        {JSON.stringify(entry.arguments, null, 2)}
                      </pre>
                    )}
                    {entry.content && (
                      <p className="mt-1 whitespace-pre-wrap leading-5 text-gms-muted">
                        {entry.content}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {result.block_reason && (
            <div className="mt-4 rounded-md border border-[#ffd8dc] bg-[#fff6f7] p-4 text-sm text-gms-danger dark:border-[#63343a] dark:bg-[#302024]">
              <p className="font-extrabold">
                Block reason
                {result.block_stage ? ` (${result.block_stage})` : ""}
              </p>
              <p className="mt-1 leading-6">{result.block_reason}</p>
              {result.blocked_policy_name && (
                <p className="mt-1 text-xs text-gms-muted">
                  Policy: {result.blocked_policy_name}
                  {result.blocked_policy_id ? ` #${result.blocked_policy_id}` : ""}
                </p>
              )}
            </div>
          )}
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
  if (result.status === "tool_error") return "tool error";
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

type StageState = "passed" | "blocked" | "idle";

type RuntimeStage = {
  label: string;
  detail: string;
  state: StageState;
};

function RuntimeProgress({ result }: { result: GuardrailsRunResponse }) {
  const stages = buildRuntimeStages(result);

  return (
    <div>
      <div className="flex flex-col gap-3 md:flex-row md:items-stretch">
        {stages.map((stage, index) => (
          <div key={stage.label} className="flex flex-1 items-center gap-3">
            <div
              className={`flex min-h-[74px] flex-1 flex-col justify-center rounded-lg border px-4 ${stageClass(stage.state)}`}
            >
              <span className="text-xs font-extrabold uppercase tracking-[0.08em]">
                {stage.label}
              </span>
              <span className="mt-1 text-sm font-semibold">
                {stage.detail}
              </span>
            </div>
            {index < stages.length - 1 && (
              <span className="hidden h-[2px] w-7 bg-gms-line md:block" />
            )}
          </div>
        ))}
      </div>
      {result.block_reason && (
        <p className="mt-3 text-xs font-semibold text-gms-danger">
          Blocked at {result.block_stage ?? "runtime"}: {result.block_reason}
        </p>
      )}
    </div>
  );
}

function buildRuntimeStages(result: GuardrailsRunResponse): RuntimeStage[] {
  const inputBlocked = result.input_rail_status === "blocked";
  const toolBlocked = result.tool_guard_status === "blocked";
  const toolErrored = result.status === "tool_error";
  const outputBlocked = result.output_rail_status === "blocked";
  const inputPassed = result.input_rail_status === "passed";
  const toolPassed =
    inputPassed && !toolBlocked && !toolErrored && result.tool_guard_status === "passed";

  return [
    {
      label: "Input",
      detail: formatRailStatus(
        result.input_rail_status,
        result.input_rail_source,
        result.input_rail_categories
      ),
      state: inputBlocked ? "blocked" : inputPassed ? "passed" : "idle"
    },
    {
      label: "Tool guard",
      detail: inputBlocked ? "not run" : formatToolGuardStatus(result),
      state:
        inputBlocked || !result.tool_guard_status
          ? "idle"
          : toolBlocked || toolErrored
          ? "blocked"
          : toolPassed
          ? "passed"
          : "idle"
    },
    {
      label: "Output",
      detail:
        inputBlocked || toolBlocked || toolErrored
          ? "not run"
          : formatRailStatus(
              result.output_rail_status,
              result.output_rail_source,
              result.output_rail_categories
            ),
      state:
        inputBlocked || toolBlocked || toolErrored || !result.output_rail_status
          ? "idle"
          : outputBlocked
          ? "blocked"
          : result.output_rail_status === "passed"
          ? "passed"
          : "idle"
    }
  ];
}

function stageClass(state: StageState) {
  if (state === "passed") {
    return "border-[#b9e7c8] bg-[#e7f7ed] text-[#257342]";
  }
  if (state === "blocked") {
    return "border-[#ffc9cf] bg-[#fff0f1] text-gms-danger";
  }
  return (
    "border-gms-line bg-white text-gms-muted dark:bg-[#252932]"
  );
}
