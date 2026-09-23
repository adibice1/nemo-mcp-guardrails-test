"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import {
  AUDIT_LOG_OUTCOMES,
  listApps,
  listAuditLogs,
  listRuntimeLogs,
  RUNTIME_LOG_OUTCOMES,
  type AuditLogOutcome,
  type RuntimeLogOutcome
} from "@/lib/api-client";
import { useAdminLogData } from "@/components/logs/use-admin-log-data";
import {
  LogsLayout, LogStatus, logDuration, logTime
} from "@/components/logs/log-ui";

const PAGE_SIZE = 25;
const AUDIT_ENTITY_TYPES = [
  "app",
  "app_connector",
  "app_policy_assignment",
  "global_policy_assignment",
  "policy",
  "policy_rules",
  "profile",
  "user",
  "user_app_access",
  "llm_config",
  "allowed_test_case"
] as const;

type LogView = "traffic" | "audit";

export default function LogsPage() {
  const [view, setView] = useState<LogView>("traffic");

  return (
    <LogsLayout title="Logs">
      <div role="tablist" aria-label="Log views" className="mt-6 grid grid-cols-2 border-b border-gms-line">
        {(["traffic", "audit"] as const).map((option) => (
          <button
            key={option}
            type="button"
            role="tab"
            aria-selected={view === option}
            onClick={() => setView(option)}
            className={`min-h-[44px] border-b-2 px-3 py-3 text-sm font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-gms-blue ${
              view === option
                ? "border-gms-blue text-gms-blue"
                : "border-transparent text-gms-muted hover:text-gms-blue"
            }`}
          >
            {option === "traffic" ? "Traffic Logs" : "Audit Logs"}
          </button>
        ))}
      </div>
      {view === "traffic" ? <TrafficLogs /> : <AuditLogs />}
    </LogsLayout>
  );
}

function TrafficLogs() {
  const [filters, setFilters] = useState({
    appId: "",
    outcome: "" as RuntimeLogOutcome | "",
    offset: 0
  });
  const loadApps = useCallback((signal: AbortSignal) => listApps(signal), []);
  const loadLogs = useCallback(
    (signal: AbortSignal) => listRuntimeLogs({
      appId: filters.appId ? Number(filters.appId) : undefined,
      outcome: filters.outcome || undefined,
      offset: filters.offset
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
    <>
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
        <RefreshButton
          label="Refresh traffic logs"
          disabled={logs.loading || apps.loading}
          onClick={() => { logs.retry(); apps.retry(); }}
        />
      </div>
      {apps.error && !logs.error && (
        <p role="alert" className="mt-4 text-sm text-gms-danger">
          App filter unavailable: {apps.error}
        </p>
      )}
      <LogRequestState
        loading={logs.loading}
        error={logs.error}
        empty={records.length === 0}
        emptyMessage="No traffic logs found."
      />
      {!logs.loading && !logs.error && records.length > 0 && (
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
                    href={`/logs/${record.request_id}`}
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
      {!logs.loading && !logs.error && (
        <Pagination
          offset={filters.offset}
          itemCount={records.length}
          itemLabel="requests"
          hasMore={Boolean(logs.data?.has_more)}
          atLimit={atLimit}
          onOffsetChange={(offset) => setFilters({ ...filters, offset })}
        />
      )}
    </>
  );
}

function AuditLogs() {
  const [filters, setFilters] = useState({
    entityType: "",
    outcome: "" as AuditLogOutcome | "",
    offset: 0
  });
  const loadLogs = useCallback(
    (signal: AbortSignal) => listAuditLogs({
      entityType: filters.entityType || undefined,
      outcome: filters.outcome || undefined,
      offset: filters.offset
    }, signal),
    [filters]
  );
  const logs = useAdminLogData(loadLogs);
  const records = logs.data?.items ?? [];
  const atLimit = filters.offset + PAGE_SIZE > 10000;

  return (
    <>
      <div className="mt-8 flex flex-wrap items-end gap-4">
        <label className="w-full min-w-0 flex-none text-sm font-semibold sm:max-w-xs sm:flex-1">
          Entity
          <select
            className="detail-input mt-2 capitalize"
            value={filters.entityType}
            onChange={(event) => setFilters({
              ...filters, entityType: event.target.value, offset: 0
            })}
          >
            <option value="">All entities</option>
            {AUDIT_ENTITY_TYPES.map((entity) => (
              <option key={entity} value={entity}>{entity.replaceAll("_", " ")}</option>
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
              outcome: event.target.value as AuditLogOutcome | "",
              offset: 0
            })}
          >
            <option value="">All outcomes</option>
            {AUDIT_LOG_OUTCOMES.map((outcome) => (
              <option key={outcome} value={outcome}>{outcome}</option>
            ))}
          </select>
        </label>
        <RefreshButton
          label="Refresh audit logs"
          disabled={logs.loading}
          onClick={logs.retry}
        />
      </div>
      <LogRequestState
        loading={logs.loading}
        error={logs.error}
        empty={records.length === 0}
        emptyMessage="No audit logs found."
      />
      {!logs.loading && !logs.error && records.length > 0 && (
        <div className="mt-8 overflow-x-auto">
          <div className="min-w-[980px]">
            <div
              aria-hidden="true"
              className="grid grid-cols-[190px_1fr_180px_250px_130px] gap-4 px-4 text-sm text-gms-muted"
            >
              <span>Actor</span><span>Action</span><span>Entity</span>
              <span>Time (UTC)</span><span>Outcome</span>
            </div>
            <ul className="mt-3 space-y-3">
              {records.map((record) => (
                <li
                  key={record.id}
                  className="grid min-h-[68px] grid-cols-[190px_1fr_180px_250px_130px] items-center gap-4 rounded-md border border-gms-line px-4 py-3 text-sm text-gms-text dark:bg-[#20242c]"
                >
                  <span className="min-w-0 break-words font-semibold">
                    {record.actor_email ?? "Unauthenticated"}
                  </span>
                  <span className="break-words font-mono text-xs">
                    {record.action}
                    <span className="mt-1 block break-all font-sans text-gms-muted">
                      {record.http_method} {record.target_path}
                    </span>
                  </span>
                  <span className="capitalize">{record.entity_type.replaceAll("_", " ")}</span>
                  <span className="text-xs">{logTime(record.occurred_at)}</span>
                  <span><LogStatus value={record.outcome} /></span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {!logs.loading && !logs.error && (
        <Pagination
          offset={filters.offset}
          itemCount={records.length}
          itemLabel="events"
          hasMore={Boolean(logs.data?.has_more)}
          atLimit={atLimit}
          onOffsetChange={(offset) => setFilters({ ...filters, offset })}
        />
      )}
    </>
  );
}

function RefreshButton({
  label, disabled, onClick
}: {
  label: string;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-gms-blue text-white shadow-button disabled:opacity-50"
    >
      <RefreshCw className="h-5 w-5" />
    </button>
  );
}

function LogRequestState({
  loading, error, empty, emptyMessage
}: {
  loading: boolean;
  error: string | null;
  empty: boolean;
  emptyMessage: string;
}) {
  if (error) return <p role="alert" className="mt-6 text-sm text-gms-danger">{error}</p>;
  if (loading) return <p role="status" className="mt-6 text-sm text-gms-muted">Loading logs...</p>;
  if (empty) {
    return <p role="status" className="py-12 text-center text-sm text-gms-muted">{emptyMessage}</p>;
  }
  return null;
}

function Pagination({
  offset, itemCount, itemLabel, hasMore, atLimit, onOffsetChange
}: {
  offset: number;
  itemCount: number;
  itemLabel: string;
  hasMore: boolean;
  atLimit: boolean;
  onOffsetChange: (offset: number) => void;
}) {
  return (
    <>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm">
        <button
          type="button"
          aria-label="Previous page"
          title="Previous page"
          disabled={offset === 0}
          onClick={() => onOffsetChange(offset - PAGE_SIZE)}
          className="flex h-9 w-9 items-center justify-center text-gms-blue disabled:opacity-40"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <span aria-live="polite">Page {offset / PAGE_SIZE + 1}</span>
        <button
          type="button"
          aria-label="Next page"
          title="Next page"
          disabled={!hasMore || atLimit}
          onClick={() => onOffsetChange(offset + PAGE_SIZE)}
          className="flex h-9 w-9 items-center justify-center text-gms-blue disabled:opacity-40"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
        <span className="text-gms-muted">{itemCount} {itemLabel}</span>
      </div>
      {atLimit && hasMore && (
        <p role="status" className="mt-3 text-center text-sm text-gms-muted">
          Pagination limit reached.
        </p>
      )}
    </>
  );
}
