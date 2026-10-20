"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CreateLlmConfigModal } from "@/components/apps/create-llm-config-modal";
import { loadManagementSession } from "@/lib/management-auth";
import {
  createLlmConfig, listAppLlmGrants, listAppLlmOptions, listLlmConfigs,
  setAppLlmGrant, updateApp, type AppLlmGrant, type AppLlmOptions,
  type AppUpdatePayload, type ClientApp, type LlmConfig, type LlmConfigCreatePayload
} from "@/lib/api-client";

type Purpose = "main" | "guardrail";
const selection = (id: number | null) => id === null ? "default" : String(id);
const configId = (value: string) => value === "default" ? null : Number(value);

export function AppModels({ app, onUpdated }: {
  app: ClientApp; onUpdated: (app: ClientApp) => void;
}) {
  const loadVersion = useRef(0);
  const [isAdmin, setIsAdmin] = useState(false);
  const [options, setOptions] = useState<Partial<Record<Purpose, AppLlmOptions>>>({});
  const [catalogue, setCatalogue] = useState<LlmConfig[]>([]);
  const [grants, setGrants] = useState<AppLlmGrant[]>([]);
  const [main, setMain] = useState(selection(app.main_llm_config_id));
  const [guardrail, setGuardrail] = useState(selection(app.guardrail_llm_config_id));
  const [grantModel, setGrantModel] = useState("default");
  const [grantPurpose, setGrantPurpose] = useState<Purpose>("main");
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { setIsAdmin(loadManagementSession()?.user.system_role === "admin"); }, []);
  useEffect(() => {
    setMain(selection(app.main_llm_config_id));
    setGuardrail(selection(app.guardrail_llm_config_id));
  }, [app.main_llm_config_id, app.guardrail_llm_config_id]);

  const reload = useCallback(async () => {
    const version = ++loadVersion.current;
    const [mainOptions, guardrailOptions, models, approvals] = await Promise.all([
      listAppLlmOptions(app.id, "main"), listAppLlmOptions(app.id, "guardrail"),
      isAdmin ? listLlmConfigs() : Promise.resolve([] as LlmConfig[]),
      isAdmin ? listAppLlmGrants(app.id) : Promise.resolve([] as AppLlmGrant[])
    ]);
    if (version !== loadVersion.current) return;
    setOptions({ main: mainOptions, guardrail: guardrailOptions });
    setCatalogue(models);
    setGrants(approvals);
  }, [app.id, isAdmin]);

  useEffect(() => {
    void reload().catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load model profiles."));
    return () => { loadVersion.current += 1; };
  }, [reload]);

  async function save() {
    const payload: AppUpdatePayload = {};
    if (main !== selection(app.main_llm_config_id)) payload.main_llm_config_id = configId(main);
    if (isAdmin && guardrail !== selection(app.guardrail_llm_config_id)) payload.guardrail_llm_config_id = configId(guardrail);
    setBusy(true); setError(""); setMessage("");
    try {
      onUpdated(await updateApp(app.id, payload));
      await reload();
      setMessage("Model selections saved.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save model selections.");
    } finally { setBusy(false); }
  }

  async function approve(purpose: Purpose, id: number | null, enabled: boolean) {
    setBusy(true); setError(""); setMessage("");
    try {
      await setAppLlmGrant(app.id, purpose, id, enabled);
      await reload();
      setMessage(enabled ? "Model access approved. Select the profile above to use it." : "Model access revoked.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update model access.");
    } finally { setBusy(false); }
  }

  async function create(payload: LlmConfigCreatePayload) {
    setError(""); setMessage("");
    try {
      const model = await createLlmConfig(payload);
      await reload();
      setGrantModel(String(model.id));
      setMessage("Profile created. Approve it for each required purpose before selection.");
      return true;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not create model profile.");
      return false;
    }
  }

  function selector(purpose: Purpose, value: string, change: (value: string) => void) {
    const choices = options[purpose];
    const available = value === "default" ? choices?.environment_default_allowed
      : choices?.configs.some((config) => String(config.id) === value);
    return <select aria-label={purpose === "main" ? "Main agent model" : "Guardrail model"}
      className="detail-input mt-2" value={value}
      disabled={busy || !choices || (purpose === "guardrail" && !isAdmin)}
      onChange={(event) => change(event.target.value)}>
      {!available && <option value={value} disabled>Current selection unavailable</option>}
      {choices?.environment_default_allowed && <option value="default">Azure environment default</option>}
      {choices?.configs.map((config) => <option key={config.id} value={String(config.id)}>
        {config.name} ({config.model_name})
      </option>)}
    </select>;
  }

  const dirty = main !== selection(app.main_llm_config_id)
    || (isAdmin && guardrail !== selection(app.guardrail_llm_config_id));
  const mainAllowed = main === "default" ? options.main?.environment_default_allowed
    : options.main?.configs.some((config) => String(config.id) === main);
  const guardrailAllowed = guardrail === "default" ? options.guardrail?.environment_default_allowed
    : options.guardrail?.configs.some((config) => String(config.id) === guardrail);

  return <section className="max-w-[1000px] space-y-7">
    <div>
      <h2 className="text-2xl font-extrabold text-gms-text">Models</h2>
      <p className="mt-2 text-sm text-gms-muted">Select approved profiles for the agent and policy checks.
        Profiles can use Azure or a compatible API gateway serving other providers.</p>
    </div>
    <div className="grid gap-6 md:grid-cols-2">
      <label className="text-sm font-semibold text-gms-text">Main agent
        {selector("main", main, setMain)}
      </label>
      <label className="text-sm font-semibold text-gms-text">Guardrail classifier
        {selector("guardrail", guardrail, setGuardrail)}
      </label>
    </div>
    {!isAdmin && <p className="text-sm text-gms-muted">An administrator manages model approvals and the guardrail selection.</p>}
    <button type="button" className="rounded-md bg-gms-blue px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
      disabled={!dirty || busy || !mainAllowed || (isAdmin && !guardrailAllowed)} onClick={() => void save()}>
      Save model selections
    </button>
    {isAdmin && <div className="space-y-4 border-t border-gms-line pt-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-bold text-gms-text">Approve model access for this app</h3>
        <button type="button" className="text-sm font-semibold text-gms-blue" onClick={() => { setError(""); setCreating(true); }}>Add model profile</button>
      </div>
      <div className="flex flex-wrap gap-3">
        <select aria-label="Profile to approve" className="detail-input max-w-[400px]" value={grantModel}
          disabled={busy} onChange={(event) => setGrantModel(event.target.value)}>
          <option value="default">Azure environment default</option>
          {catalogue.filter((model) => model.enabled).map((model) => <option key={model.id} value={String(model.id)}>{model.name}</option>)}
        </select>
        <select aria-label="Model approval purpose" className="detail-input max-w-[200px]" value={grantPurpose}
          disabled={busy} onChange={(event) => setGrantPurpose(event.target.value as Purpose)}>
          <option value="main">Main agent</option><option value="guardrail">Guardrail classifier</option>
        </select>
        <button type="button" disabled={busy} className="text-sm font-semibold text-gms-blue"
          onClick={() => void approve(grantPurpose, configId(grantModel), true)}>Approve access</button>
      </div>
      <ul className="space-y-2 text-sm text-gms-text">
        {grants.filter((grant) => grant.enabled).map((grant) => <li key={grant.id} className="flex items-center justify-between gap-4">
          <span>{grant.config_name} — {grant.purpose === "main" ? "Main agent" : "Guardrail classifier"}</span>
          <button type="button" disabled={busy} className="font-semibold text-gms-danger"
            onClick={() => void approve(grant.purpose, grant.llm_config_id, false)}>Revoke access</button>
        </li>)}
      </ul>
      <p className="text-xs text-gms-muted">Approve a model only after testing the required tool calling and policy checks.
        Revoking the selected profile prevents future runtime requests until another approved profile is selected.</p>
      <CreateLlmConfigModal open={creating} error={error} onClose={() => setCreating(false)} onSubmit={create} />
    </div>}
    {message && <p role="status" className="text-sm text-gms-text">{message}</p>}
    {error && <p role="alert" className="text-sm text-gms-danger">{error}</p>}
  </section>;
}
