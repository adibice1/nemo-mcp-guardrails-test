"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, X } from "lucide-react";
import {
  AppTable,
  type AppSummary
} from "@/components/apps/app-table";
import {
  CreateAppModal,
  type AppDraft,
  type CreatedAppSecret
} from "@/components/apps/create-app-modal";
import { AppTopNav } from "@/components/shared/app-top-nav";
import {
  createApp,
  deleteApp,
  getEffectivePolicyAssignments,
  hasApiBaseUrl,
  listAppConnectors,
  listApps
} from "@/lib/api-client";
import { loadManagementSession } from "@/lib/management-auth";

const PAGE_SIZE = 8;

export default function AppsPage() {
  const router = useRouter();
  const [apps, setApps] = useState<AppSummary[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  const loadApps = useCallback(async () => {
    if (!hasApiBaseUrl()) {
      setLoading(false);
      setError("Configure NEXT_PUBLIC_API_BASE_URL to manage applications.");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const records = await listApps();
      const summaries = await Promise.all(
        records.map(async (app) => {
          const [connectors, policies] = await Promise.all([
            listAppConnectors(app.client_id),
            getEffectivePolicyAssignments(app.client_id)
          ]);
          return {
            ...app,
            connectorCount: connectors.filter((connector) => connector.enabled)
              .length,
            policyCount: policies.enabled_assignment_count
          };
        })
      );
      setApps(summaries);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Could not load applications."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setIsAdmin(loadManagementSession()?.user.system_role === "admin");
    void loadApps();
  }, [loadApps]);

  const visibleApps = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return needle
      ? apps.filter(
          (app) =>
            app.name.toLowerCase().includes(needle) ||
            app.client_id.toLowerCase().includes(needle)
        )
      : apps;
  }, [apps, search]);

  const totalPages = Math.max(1, Math.ceil(visibleApps.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginatedApps = visibleApps.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  async function handleCreate(draft: AppDraft): Promise<CreatedAppSecret | null> {
    try {
      setError("");
      const app = await createApp({
        name: draft.name,
        authorized: true,
        main_llm_config_id: null,
        guardrail_llm_config_id: null
      });
      await loadApps();
      setNotice(`${app.name} was created. Copy its API key before closing.`);
      return {
        name: app.name,
        apiKey: app.api_key,
        notice: app.api_key_notice
      };
    } catch (createError) {
      setError(
        createError instanceof Error
          ? createError.message
          : "Could not create application."
      );
      return null;
    }
  }

  async function handleDelete(app: AppSummary) {
    const confirmed = window.confirm(
      `Delete "${app.name}"? Its connector links, policy assignments and conversation history will also be removed.`
    );
    if (!confirmed) {
      return;
    }
    try {
      await deleteApp(app.id);
      await loadApps();
      setNotice(`${app.name} was deleted.`);
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "Could not delete application."
      );
    }
  }

  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="apps" />
      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-8 py-12 shadow-shell transition-colors dark:bg-[#1b1e25] lg:px-20">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-normal text-gms-text lg:text-[42px]">
              Applications
            </h1>
            <p className="mt-3 max-w-xl text-sm text-gms-muted">
              Manage applications that consume GMS policies and guarded runtime
              services.
            </p>
          </div>
          <div className="flex flex-col items-stretch gap-7 lg:items-end">
            <label className="relative block w-full lg:w-[405px]">
              <input
                className="h-11 w-full rounded-xl border border-gms-line bg-white px-4 pr-11 text-sm text-gms-text shadow-field outline-none placeholder:text-gms-muted dark:bg-[#252932]"
                placeholder="Search applications"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
              <Search className="absolute right-5 top-3 h-5 w-5 text-gms-text" />
            </label>
            {isAdmin && (
              <button
                className="inline-flex h-10 w-full items-center justify-center gap-3 rounded-md bg-gms-blue px-4 text-sm font-medium text-white shadow-button lg:w-[170px]"
                type="button"
                onClick={() => setModalOpen(true)}
              >
                <Plus className="h-5 w-5" />
                Create App
              </button>
            )}
          </div>
        </div>

        <AppTable
          apps={paginatedApps}
          page={safePage}
          pageSize={PAGE_SIZE}
          totalCount={visibleApps.length}
          onDelete={handleDelete}
          onOpen={(app) => router.push(`/apps/${encodeURIComponent(app.client_id)}`)}
          onPageChange={setPage}
        />

        {loading && <p className="mt-3 text-xs text-gms-muted">Loading applications...</p>}
        {error && <p className="mt-3 text-xs text-gms-danger">{error}</p>}
      </section>

      <CreateAppModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleCreate}
      />

      {notice && (
        <div className="fixed right-6 top-6 z-[70] flex max-w-md items-start gap-4 rounded-md border border-[#8bc9a7] bg-white px-5 py-4 text-sm text-[#245d3b] shadow-modal dark:bg-[#252932] dark:text-[#9ee1b7]">
          <span>{notice}</span>
          <button type="button" onClick={() => setNotice("")}>
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </main>
  );
}
