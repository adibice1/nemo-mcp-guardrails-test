"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import {
  listApps,
  listRuntimeLogs,
  RUNTIME_LOG_OUTCOMES,
  type RuntimeLogOutcome
} from "@/lib/api-client";
import { useAdminLogData } from "@/components/logs/use-admin-log-data";
import {
  LogsLayout, LogStatus, logDuration, logTime
} from "@/components/logs/log-ui";

const PAGE_SIZE = 25;

export default function LogsPage() {
  const [filters, setFilters] = useState({
    view: "traffic" as "traffic" | "user",
    appId: "",
    outcome: "" as RuntimeLogOutcome | "",
    offset: 0
  });
  const loadApps = useCallback((signal: AbortSignal) => listApps(signal), []);
  const loadLogs = useCallback(
    (signal: AbortSignal) => listRuntimeLogs({
      appId: filters.appId ? Number(filters.appId) : undefined,
      outcome: filters.outcome || undefined,
      offset: filters.offset,
      userContentOnly: filters.view === "user"
    }, signal),
    [filters]
  );
  const apps = useAdminLogData(loadApps);
  const logs = useAdminLogData(loadLogs);
  const records = logs.data?.items ?? [];
  const page = filters.offset / PAGE_SIZE + 1;
  const atLimit = filters.offset + PAGE_SIZE > 10000;

  function appName(id: number | null) {
    if (id === null) return "No app reference";
    return apps.data?.find((app) => app.id === id)?.name ?? `App ${id}`;
  }

  return (
    <LogsLayout title="Logs">
      <div role="group" aria-label="Log views" className="mt-6 grid grid-cols-2 border-b border-gms-line">
        {(["traffic", "user"] as const).map((view) => (
          <button
            key={view}
            type="button"
            aria-pressed={filters.view === view}
            onClick={() => setFilters((current) => ({ ...current, view, offset: 0 }))}
            className={`min-h-[44px] border-b-2 px-3 py-3 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-gms-blue ${
              filters.view === view
                ? "border-gms-blue text-gms-blue"
                : "border-transparent text-gms-muted hover:text-gms-blue"
            }`}
          >
            {view === "traffic" ? "Traffic Logs" : "User Logs"}
          </button>
        ))}
      </div>
      <div className="mt-8 flex flex-wrap items-end gap-4">
        <label className="w-full min-w-0 flex-none text-sm font-semibold sm:max-w-xs sm:flex-1">
          App
          <select
            className="detail-input mt-2"
            value={filters.appId}
            disabled={apps.loading || !apps.data}
            onChange={(event) => setFilters({
              ...filters, appId: event.target.value, offset: 0
            })}
          >
            <option value="">All apps</option>
            {apps.data?.map((app) => (
              <option key={app.id} value={app.id}>{app.name}</option>
            ))}
          </select>
        </label>
        <label className="w-full min-w-0 flex-none text-sm font-semibold sm:max-w-xs sm:flex-1">
          Outcome
          <select
            className="detail-input mt-2 capitalize"
            value={filters.outcome}
            onChange={(event) => setFilters({
              ...filters,
              outcome: event.target.value as RuntimeLogOutcome | "",
              offset: 0
            })}
          >
            <option value="">All outcomes</option>
            {RUNTIME_LOG_OUTCOMES.map((outcome) => (
              <option key={outcome} value={outcome}>
                {outcome.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          aria-label="Refresh logs"
          title="Refresh logs"
          disabled={logs.loading || apps.loading}
          onClick={() => { logs.retry(); apps.retry(); }}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-gms-blue text-white shadow-button disabled:opacity-50"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>

      {apps.error && !logs.error && (
        <p role="alert" className="mt-4 text-sm text-gms-danger">
          App filter unavailable: {apps.error}
        </p>
      )}
      {logs.error && (
        <p role="alert" className="mt-6 text-sm text-gms-danger">{logs.error}</p>
      )}
      {logs.loading && (
        <p role="status" className="mt-6 text-sm text-gms-muted">Loading logs...</p>
      )}
      {!logs.loading && !logs.error && (
        <>
          {records.length === 0 ? (
            <p role="status" className="py-12 text-center text-sm text-gms-muted">
              {filters.view === "user" ? "No user logs found." : "No traffic logs found."}
            </p>
          ) : (
            <div className="mt-8 overflow-x-auto">
              <div className="min-w-[850px]">
                <div
                  aria-hidden="true"
                  className="grid grid-cols-[220px_1fr_220px_130px_110px] gap-4 px-4 text-sm text-gms-muted"
                >
                  <span>Request</span><span>App</span><span>Started (UTC)</span>
                  <span>Outcome</span><span>Duration</span>
                </div>
                <ul className="mt-3 space-y-3">
                  {records.map((record) => (
                    <li key={record.request_id}>
                      <Link
                        href={`/logs/${record.request_id}${filters.view === "user" ? "?view=user" : ""}`}
                        prefetch={false}
                        aria-label={`Open request ${record.request_id}, ${appName(record.app_id)}, ${record.outcome}`}
                        className="grid min-h-[62px] grid-cols-[220px_1fr_220px_130px_110px] items-center gap-4 rounded-md border border-gms-line px-4 py-3 text-sm text-gms-text transition hover:border-gms-blue hover:bg-gms-blue hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-gms-blue dark:bg-[#20242c]"
                      >
                        <span className="break-all font-mono text-xs">{record.request_id}</span>
                        <span className="min-w-0 break-words font-semibold">{appName(record.app_id)}</span>
                        <span className="text-xs">{logTime(record.started_at)}</span>
                        <span><LogStatus value={record.outcome} /></span>
                        <span>{logDuration(record.duration_ms)}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm">
            <button
              type="button"
              aria-label="Previous page"
              title="Previous page"
              disabled={filters.offset === 0}
              onClick={() => setFilters({ ...filters, offset: filters.offset - PAGE_SIZE })}
              className="flex h-9 w-9 items-center justify-center text-gms-blue disabled:opacity-40"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <span aria-live="polite">Page {page}</span>
            <button
              type="button"
              aria-label="Next page"
              title="Next page"
              disabled={!logs.data?.has_more || atLimit}
              onClick={() => setFilters({ ...filters, offset: filters.offset + PAGE_SIZE })}
              className="flex h-9 w-9 items-center justify-center text-gms-blue disabled:opacity-40"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            <span className="text-gms-muted">{records.length} requests</span>
          </div>
          {atLimit && logs.data?.has_more && (
            <p role="status" className="mt-3 text-center text-sm text-gms-muted">
              Pagination limit reached.
            </p>
          )}
        </>
      )}
    </LogsLayout>
  );
}
