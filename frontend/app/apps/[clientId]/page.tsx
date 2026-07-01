"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Bot } from "lucide-react";
import { AppConnectors } from "@/components/apps/app-connectors";
import { AppLlmSettings } from "@/components/apps/app-llm-settings";
import { AppOverview } from "@/components/apps/app-overview";
import { AppPolicySummary } from "@/components/apps/app-policy-summary";
import { AppRuntimeTest } from "@/components/apps/app-runtime-test";
import { AppTopNav } from "@/components/shared/app-top-nav";
import { getApp, type ClientApp } from "@/lib/api-client";
import { cn } from "@/lib/utils";

type AppTab = "overview" | "connectors" | "llm" | "policies" | "runtime";

const tabs: Array<{ key: AppTab; label: string }> = [
  { key: "overview", label: "Overview" },
  { key: "connectors", label: "Connectors" },
  { key: "llm", label: "LLM" },
  { key: "policies", label: "Policies" },
  { key: "runtime", label: "Runtime Test" }
];

export default function AppDetailPage({
  params
}: {
  params: { clientId: string };
}) {
  const router = useRouter();
  const routeClientId = decodeURIComponent(params.clientId);
  const [app, setApp] = useState<ClientApp | null>(null);
  const [activeTab, setActiveTab] = useState<AppTab>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadApp = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      setApp(await getApp(routeClientId));
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Could not load application."
      );
    } finally {
      setLoading(false);
    }
  }, [routeClientId]);

  useEffect(() => {
    void loadApp();
  }, [loadApp]);

  function handleUpdated(updated: ClientApp) {
    setApp(updated);
    if (updated.client_id !== routeClientId) {
      router.replace(`/apps/${encodeURIComponent(updated.client_id)}`);
    }
  }

  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="apps" />
      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-8 py-10 shadow-shell transition-colors dark:bg-[#1b1e25] lg:px-16">
        <button
          className="inline-flex items-center gap-2 text-sm font-semibold text-gms-blue"
          type="button"
          onClick={() => router.push("/apps")}
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Apps
        </button>

        {app && (
          <>
            <div className="mt-7 flex items-center gap-4">
              <div className="flex items-center gap-4">
                <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-gms-blue-soft text-gms-blue">
                  <Bot className="h-7 w-7" />
                </span>
                <div>
                  <h1 className="text-3xl font-extrabold text-gms-text lg:text-[38px]">
                    {app.name}
                  </h1>
                  <p className="mt-1 font-mono text-sm text-gms-muted">
                    {app.client_id}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-9 overflow-x-auto border-b border-gms-line">
              <nav className="flex min-w-max gap-8">
                {tabs.map((tab) => (
                  <button
                    key={tab.key}
                    className={cn(
                      "relative pb-3 text-sm font-bold text-gms-muted transition hover:text-gms-blue",
                      activeTab === tab.key && "text-gms-blue"
                    )}
                    type="button"
                    onClick={() => setActiveTab(tab.key)}
                  >
                    {tab.label}
                    {activeTab === tab.key && (
                      <span className="absolute bottom-0 left-0 h-[3px] w-full rounded-full bg-gms-blue" />
                    )}
                  </button>
                ))}
              </nav>
            </div>

            <div className="py-9">
              {activeTab === "overview" && (
                <AppOverview app={app} onUpdated={handleUpdated} />
              )}
              {activeTab === "connectors" && (
                <AppConnectors clientId={app.client_id} />
              )}
              {activeTab === "llm" && (
                <AppLlmSettings app={app} onUpdated={handleUpdated} />
              )}
              {activeTab === "policies" && <AppPolicySummary app={app} />}
              {activeTab === "runtime" && (
                <AppRuntimeTest clientId={app.client_id} />
              )}
            </div>
          </>
        )}

        {loading && <p className="mt-8 text-sm text-gms-muted">Loading application...</p>}
        {error && <p className="mt-8 text-sm text-gms-danger">{error}</p>}
      </section>
    </main>
  );
}
