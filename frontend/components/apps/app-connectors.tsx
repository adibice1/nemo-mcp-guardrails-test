"use client";

import { useCallback, useEffect, useState } from "react";
import { Link2, Plus, Trash2 } from "lucide-react";
import { FaMicrosoft } from "react-icons/fa6";
import { SiGithub } from "react-icons/si";
import {
  deleteAppConnector,
  listAppConnectors,
  saveAppConnector,
  updateAppConnector,
  type AppConnector
} from "@/lib/api-client";

export function AppConnectors({ clientId }: { clientId: string }) {
  const [connectors, setConnectors] = useState<AppConnector[]>([]);
  const [connectorName, setConnectorName] = useState("github");
  const [credentialReference, setCredentialReference] = useState(
    "env:GITHUB_PERSONAL_ACCESS_TOKEN"
  );
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const loadConnectors = useCallback(async () => {
    try {
      setLoading(true);
      setConnectors(await listAppConnectors(clientId));
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Could not load connectors."
      );
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    void loadConnectors();
  }, [loadConnectors]);

  async function handleLink() {
    if (connectorName !== "github") {
      setMessage("SharePoint runtime support is coming soon.");
      return;
    }
    try {
      await saveAppConnector(clientId, {
        connector_name: connectorName,
        credential_reference: credentialReference.trim() || null,
        enabled: true
      });
      await loadConnectors();
      setMessage("GitHub connector saved.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not link connector.");
    }
  }

  async function handleToggle(connector: AppConnector) {
    try {
      await updateAppConnector(clientId, connector.connector_name, {
        enabled: !connector.enabled
      });
      await loadConnectors();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not update connector.");
    }
  }

  async function handleDelete(connector: AppConnector) {
    if (!window.confirm(`Unlink ${connector.connector_display_name}?`)) {
      return;
    }
    try {
      await deleteAppConnector(clientId, connector.connector_name);
      await loadConnectors();
      setMessage(`${connector.connector_display_name} was unlinked.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not unlink connector.");
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-extrabold text-gms-text">Connectors</h2>
      <p className="mt-2 text-sm text-gms-muted">
        Connect this application to external tools used by its guarded agent.
      </p>

      <div className="mt-7 grid gap-4 rounded-md border border-gms-line bg-[#f9fbff] p-5 dark:bg-[#20242c] md:grid-cols-[180px_1fr_auto] md:items-end">
        <label className="text-sm font-bold text-gms-text">
          Connector
          <select
            className="detail-input mt-2"
            value={connectorName}
            onChange={(event) => {
              const value = event.target.value;
              setConnectorName(value);
              setCredentialReference(
                value === "github" ? "env:GITHUB_PERSONAL_ACCESS_TOKEN" : ""
              );
            }}
          >
            <option value="github">GitHub</option>
            <option value="sharepoint">SharePoint (Coming soon)</option>
          </select>
        </label>
        <label className="text-sm font-bold text-gms-text">
          Credential Reference
          <input
            className="detail-input mt-2 font-mono text-xs"
            disabled={connectorName === "sharepoint"}
            placeholder="env:VARIABLE_NAME"
            value={credentialReference}
            onChange={(event) => setCredentialReference(event.target.value)}
          />
        </label>
        <button
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-gms-blue px-5 text-sm font-semibold text-white shadow-button disabled:opacity-50"
          disabled={connectorName === "sharepoint"}
          type="button"
          onClick={handleLink}
        >
          <Plus className="h-4 w-4" />
          Link Connector
        </button>
      </div>

      <div className="mt-6 space-y-3">
        {connectors.map((connector) => (
          <div
            key={connector.id}
            className="grid min-h-[72px] grid-cols-[60px_1fr_1.5fr_130px_70px] items-center rounded-md border border-gms-line bg-white px-4 text-sm text-gms-text dark:bg-[#20242c]"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-gms-blue-soft">
              {connector.connector_name === "github" ? (
                <SiGithub className="h-6 w-6 dark:text-white" />
              ) : (
                <FaMicrosoft className="h-6 w-6 text-[#038387]" />
              )}
            </span>
            <span>
              <strong>{connector.connector_display_name}</strong>
              <span className="mt-1 block text-xs text-gms-muted">
                {connector.connector_enabled ? "Connector available" : "Connector disabled"}
              </span>
            </span>
            <code className="truncate text-xs text-gms-muted">
              {connector.credential_reference || "Default environment credential"}
            </code>
            <button
              className={`inline-flex w-fit rounded-full px-3 py-1 text-xs font-semibold ${
                connector.enabled
                  ? "bg-[#e7f7ed] text-[#257342]"
                  : "bg-[#eeeeee] text-[#676b76]"
              }`}
              type="button"
              onClick={() => handleToggle(connector)}
            >
              {connector.enabled ? "Enabled" : "Disabled"}
            </button>
            <button
              aria-label={`Unlink ${connector.connector_display_name}`}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-[#fff0f1] text-gms-danger"
              type="button"
              onClick={() => handleDelete(connector)}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
        {!loading && connectors.length === 0 && (
          <div className="rounded-md border border-dashed border-gms-line py-12 text-center text-sm text-gms-muted">
            <Link2 className="mx-auto mb-3 h-7 w-7" />
            No connectors linked yet.
          </div>
        )}
      </div>
      {message && <p className="mt-4 text-sm text-gms-muted">{message}</p>}
    </div>
  );
}
