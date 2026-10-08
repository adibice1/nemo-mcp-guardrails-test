"use client";

import { useEffect, useId, useRef, useState } from "react";
import { ArrowDown, ArrowRight, Sparkles } from "lucide-react";
import {
  hasApiBaseUrl, suggestPolicy, type PolicyConnectorOption,
  type PolicyAssistantResult, type PolicyAssistantSuggestion
} from "@/lib/api-client";
import { loadManagementSession } from "@/lib/management-auth";
import type { PolicyDraft } from "@/components/policies/create-policy-modal";

type SampleAction = "merge" | "create";
type Props = {
  policyType: "input" | "output";
  policyOptions: PolicyConnectorOption[];
  disabled?: boolean;
  enableLive?: boolean;
  onUseDraft: (draft: Omit<PolicyDraft, "global">) => void;
};
const prompts: Record<SampleAction, string> = {
  merge: "Prevent all merging of pull requests from any non-staging branch to a production branch",
  create: "Prevent creation of pull requests from any non-staging branch to a production branch"
};
const actions: SampleAction[] = ["merge", "create"];
const buttonClass = "rounded-md border border-gms-blue px-3 py-2 text-sm text-gms-blue disabled:opacity-50";

function sampleSuggestion(action: SampleAction): PolicyAssistantSuggestion {
  return {
    policy_type: "input", connector: "github", action, resource: "pull_request",
    custom_resource: "whose target branch is production and whose source branch is not staging",
    name: action === "merge" ? "Block non-staging PR merges into production"
      : "Block non-staging PR creation into production",
    explanation: "Restrict requests targeting production when the source branch is not staging.",
    examples: [
      { prompt: `${action} a PR from feature into production`, expected: "block" },
      { prompt: `${action} a PR from staging into production`, expected: "not_blocked_by_this_policy" },
      { prompt: `${action} a PR from feature into staging`, expected: "not_blocked_by_this_policy" }
    ]
  };
}

const outputPrompt = 'Block any agent response that contains the word "hello"';

function outputSample(): PolicyAssistantSuggestion {
  return {
    policy_type: "output", name: 'Block the word "hello" in responses',
    output_rule: 'Do not include the word "hello" in assistant responses.',
    explanation: 'Block responses containing the word "hello", regardless of casing.',
    examples: [
      { prompt: "Hello! How can I help?", expected: "block" },
      { prompt: "Good morning.", expected: "not_blocked_by_this_policy" },
      { prompt: "shelloworld", expected: "not_blocked_by_this_policy" }
    ]
  };
}

function normalizePrompt(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, " ").replace(/[.!?]+$/, "");
}

export function PolicyAuthoringAssistant({
  policyType, policyOptions, disabled = false, enableLive = true, onUseDraft
}: Props) {
  const promptId = useId();
  const [prompt, setPrompt] = useState("");
  const [mode, setMode] = useState<"sample" | "live">("sample");
  const [liveAvailable, setLiveAvailable] = useState(false);
  const [result, setResult] = useState<PolicyAssistantResult | null>(null);
  const [selected, setSelected] = useState<PolicyAssistantSuggestion | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const requestId = useRef(0);

  useEffect(() => {
    const available = enableLive && hasApiBaseUrl() && !!loadManagementSession();
    setLiveAvailable(available);
    setMode(available ? "live" : "sample");
    return () => {
      requestId.current += 1;
      controller.current?.abort();
    };
  }, [enableLive]);

  const input = selected?.policy_type === "input" ? selected : null;
  const ruleText = selected?.policy_type === "output"
    ? selected.output_rule : input?.custom_resource ?? "";
  const connectorOption = policyOptions.find((option) => option.value === input?.connector);
  const actionOption = connectorOption?.actions.find((option) => option.value === input?.action);
  const resourceOption = actionOption?.resources.find((option) => option.value === input?.resource);

  function supports(suggestion: PolicyAssistantSuggestion) {
    if (suggestion.policy_type !== policyType) return false;
    if (suggestion.policy_type === "output") return !!suggestion.output_rule.trim();
    return policyOptions.some((connector) =>
      connector.value === suggestion.connector && connector.actions.some((action) =>
        action.value === suggestion.action && action.resources.some(
          (resource) => resource.value === suggestion.resource
        )
      )
    );
  }

  function clearPreview() {
    requestId.current += 1;
    controller.current?.abort();
    setBusy(false);
    setResult(null);
    setSelected(null);
    setMessage("");
  }

  function changePrompt(value: string) {
    clearPreview();
    setPrompt(value);
  }

  async function previewPolicy() {
    clearPreview();
    if (mode === "sample") {
      if (policyType === "output") {
        if (normalizePrompt(prompt) !== normalizePrompt(outputPrompt)) {
          setMessage("Sample mode supports the hello example. Select Live AI to describe another output policy.");
          return;
        }
        const sample = { draft: outputSample(), related: [], clarification: "" };
        setResult(sample);
        setSelected(sample.draft);
        return;
      }
      const match = actions.find(
        (action) => normalizePrompt(prompts[action]) === normalizePrompt(prompt)
      );
      if (!match) {
        setMessage("Sample mode supports the two examples. Select Live AI to describe another policy.");
        return;
      }
      const sample = {
        draft: sampleSuggestion(match),
        related: [sampleSuggestion(match === "merge" ? "create" : "merge")],
        clarification: ""
      };
      setResult(sample);
      setSelected(sample.draft);
      return;
    }
    if (!liveAvailable) {
      setMessage("Sign in to the configured GMS backend to use live AI.");
      return;
    }
    const version = ++requestId.current;
    const pending = new AbortController();
    controller.current = pending;
    setBusy(true);
    const timeout = window.setTimeout(() => pending.abort(), 45000);
    try {
      const response = await suggestPolicy(prompt.trim(), policyType, pending.signal);
      if (version !== requestId.current) return;
      setResult(response);
      setSelected(response.draft);
      setMessage(response.clarification);
    } catch (error) {
      if (version === requestId.current) {
        setMessage(error instanceof Error && error.name === "AbortError"
          ? "The AI request timed out. Please try again."
          : error instanceof Error ? error.message : "Could not generate a policy draft.");
      }
    } finally {
      window.clearTimeout(timeout);
      if (version === requestId.current) setBusy(false);
    }
  }

  return (
    <section className="mt-5 rounded-xl border border-gms-line bg-gms-blue-soft p-4" aria-label="AI policy assistant" aria-busy={busy}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="flex items-center gap-2 font-bold text-gms-text">
          <Sparkles className="h-4 w-4 text-gms-blue" aria-hidden="true" />
          AI Policy Assistant
        </h3>
        <span className="rounded-full border border-gms-line px-2 py-1 text-xs text-gms-muted">
          {mode === "live" ? "Live AI draft" : "Sample preview"}
        </span>
      </div>
      {enableLive && (
        <label className="mt-3 block text-sm text-gms-text">
          Drafting mode
          <select className="ml-2 rounded border border-gms-line bg-white p-2 dark:bg-[#252932]"
            value={mode} disabled={disabled}
            onChange={(event) => {
              clearPreview();
              setMode(event.target.value as "sample" | "live");
            }}>
            <option value="sample">Sample examples</option>
            <option value="live" disabled={!liveAvailable}>Live AI</option>
          </select>
          {!liveAvailable && <span className="mt-1 block text-xs text-gms-muted">Sign in to a configured backend to enable Live AI.</span>}
        </label>
      )}
      <label htmlFor={promptId} className="mt-4 block text-sm font-medium text-gms-text">
        Describe what you want to prevent
      </label>
      <textarea id={promptId}
        className="mt-2 min-h-[84px] w-full rounded-lg border border-gms-line bg-white p-3 text-sm text-gms-text dark:bg-[#252932]"
        placeholder={policyType === "output" ? outputPrompt : prompts.merge} value={prompt} disabled={disabled} maxLength={2000}
        onChange={(event) => changePrompt(event.target.value)}
      />
      <div className="mt-2 flex flex-wrap gap-2">
        {policyType === "output" ? (
          <button type="button" className={buttonClass} disabled={disabled}
            onClick={() => changePrompt(outputPrompt)}>
            Try hello example
          </button>
        ) : actions.map((action) => (
          <button key={action} type="button" className={buttonClass} disabled={disabled}
            onClick={() => changePrompt(prompts[action])}>
            {action === "merge" ? "Try merge example" : "Try PR creation example"}
          </button>
        ))}
        <button type="button" className="rounded-md bg-gms-blue px-3 py-2 text-sm text-white disabled:opacity-50"
          disabled={disabled || busy || prompt.trim().length < 5} onClick={() => void previewPolicy()}>
          {busy ? "Generating..." : mode === "live" ? "Generate policy" : "Preview policy"}
        </button>
      </div>
      <p className="mt-2 text-xs text-gms-muted">
        {mode === "live" ? "AI-generated drafts require review." : "Local sample responses."}
        {" "}Previewing does not save policies or run connector tools.
      </p>
      <p role="status" className="mt-2 text-sm text-gms-text">{busy ? "Generating a policy draft..." : message}</p>

      {selected && (
        <div className="mt-3 space-y-4 text-sm text-gms-text">
          <div className="rounded-lg border border-gms-line bg-white p-3 dark:bg-[#252932]">
            <h4 className="font-semibold">{selected.name}</h4>
            <p className="mt-1 text-gms-muted">{selected.explanation}</p>
            <ol aria-label="Policy flowchart" className="mt-3 flex flex-col items-center gap-2 sm:flex-row sm:flex-wrap">
              {(selected.policy_type === "output" ? ["Output", "Custom resource"] :
                ["Input", connectorOption?.label ?? input?.connector,
                  actionOption?.label ?? input?.action, resourceOption?.label ?? input?.resource]).map((step, index) => (
                <li key={index} className="flex flex-col items-center gap-2 sm:flex-row">
                  {index > 0 && <ArrowRight aria-hidden="true" className="h-4 w-4 rotate-90 text-gms-blue sm:rotate-0" />}
                  <span className="rounded-lg border border-gms-blue px-3 py-2">{step}</span>
                </li>
              ))}
            </ol>
            <ArrowDown aria-hidden="true" className="mx-auto my-2 h-4 w-4 text-gms-blue" />
            <div className="break-words rounded-lg border-2 border-gms-blue p-3 text-center">
              {selected.policy_type === "output"
                ? "Does the assistant response violate this rule?" : "Does the request match this scope?"}<br />
              <strong>{ruleText || "Any matching request"}</strong>
            </div>
            <div className="mt-2 grid grid-cols-1 gap-2 text-center sm:grid-cols-2">
              <div className="rounded-lg border border-gms-danger p-2">Yes → Block at {selected.policy_type} rail</div>
              <div className="rounded-lg border border-gms-line p-2">No → Not blocked by this policy</div>
            </div>
          </div>
          <div>
            <h4 className="font-semibold">{selected.policy_type === "output"
              ? "Suggested output-rule wording" : "Suggested custom-resource wording"}</h4>
            <p className="mt-1 break-words rounded-lg border border-gms-line p-3">
              {ruleText || "Leave blank to cover all matching resources."}
            </p>
          </div>
          <div>
            <h4 className="font-semibold">{selected.policy_type === "output"
              ? "Example assistant responses" : "Expected input-rail behaviour"}</h4>
            <ul className="mt-1 space-y-1">
              {selected.examples.map((example, index) => (
                <li key={index} className="break-words">
                  {example.prompt}: <strong>{example.expected === "block" ? "block" : "not blocked by this policy"}</strong>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-gms-muted">Illustrative expectations; no runtime tests have been run here.</p>
          </div>
          <button type="button" className={buttonClass} disabled={disabled || !supports(selected)}
            onClick={() => {
              onUseDraft(selected.policy_type === "output" ? {
                policyType: "output", connector: "", action: "", resource: "",
                customResource: "", outputRule: selected.output_rule, name: selected.name
              } : {
                policyType: "input", connector: selected.connector,
                action: selected.action, resource: selected.resource,
                customResource: selected.custom_resource, outputRule: "", name: selected.name
              });
              setMessage("Draft filled into the form below. Review or edit it before creating the policy.");
            }}>
            Use this draft
          </button>
          {!supports(selected) && <p role="status">This combination is unavailable in the current policy options.</p>}
          <p className="text-xs text-gms-muted">Using a draft replaces the policy fields below and keeps the selected scope.</p>
          {result?.draft && selected !== result.draft && (
            <button type="button" className={buttonClass} disabled={disabled}
              onClick={() => { setSelected(result.draft); setMessage(""); }}>
              Preview original policy
            </button>
          )}
          {!!result?.related.length && (
            <div className="space-y-3 border-t border-gms-line pt-3">
              <h4 className="font-semibold">Related policy suggestions</h4>
              <p className="text-xs text-gms-muted">Separate policies to review and create independently.</p>
              {result.related.map((suggestion, index) => (
                <div key={index}>
                  <p>{suggestion.name}</p>
                  <p className="mt-1 break-words text-xs text-gms-muted">{suggestion.explanation}</p>
                  <button type="button" className={buttonClass + " mt-2"} disabled={disabled}
                    onClick={() => { setSelected(suggestion); setMessage(""); }}>
                    Preview related policy
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
