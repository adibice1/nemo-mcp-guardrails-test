"use client";

import Link from "next/link";
import { useCallback } from "react";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { getRuntimeLog, getRuntimeUserLog } from "@/lib/api-client";
import { useAdminLogData } from "@/components/logs/use-admin-log-data";
import {
  LogsLayout, LogStatus, logDuration, logTime
} from "@/components/logs/log-ui";

export default function RuntimeLogDetailPage({
  params, searchParams
}: {
  params: { requestId: string };
  searchParams?: { view?: string };
}) {
  const userView = searchParams?.view === "user";
  const load = useCallback(
    async (signal: AbortSignal) => {
      const record = await getRuntimeLog(params.requestId, signal);
      const userContent = userView ? await getRuntimeUserLog(params.requestId, signal) : null;
      return { ...record, userContent };
    },
    [params.requestId, userView]
  );
  const { data, loading, error, retry } = useAdminLogData(load);

  return (
    <LogsLayout title="Runtime Request">
      <div className="mt-6 flex items-center justify-between gap-4">
        <Link href="/logs" className="inline-flex items-center gap-2 text-sm text-gms-blue">
          <ArrowLeft className="h-4 w-4" /> Logs
        </Link>
        <button
          type="button"
          aria-label="Refresh request"
          title="Refresh request"
          disabled={loading}
          onClick={retry}
          className="flex h-10 w-10 items-center justify-center rounded-md bg-gms-blue text-white disabled:opacity-50"
        >
          <RefreshCw className="h-5 w-5" />
        </button>
      </div>
      {loading && (
        <p role="status" className="mt-6 text-sm text-gms-muted">
          Loading request...
        </p>
      )}
      {error && (
        <p role="alert" className="mt-6 text-sm text-gms-danger">{error}</p>
      )}
      {data && (
        <>
          <div className="mt-6"><LogStatus value={data.outcome} /></div>
          <dl className="mt-6 grid gap-x-8 gap-y-5 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {[
              ["Request ID", data.request_id],
              ["App ID", data.app_id === null ? "No app reference" : String(data.app_id)],
              ["HTTP status", data.http_status === null ? "Not recorded" : String(data.http_status)],
              ["Started (UTC)", logTime(data.started_at)],
              ["Completed (UTC)", logTime(data.completed_at)],
              ["Duration", logDuration(data.duration_ms)],
              ["Schema version", data.schema_version]
            ].map(([label, value]) => (
              <div key={label} className="min-w-0">
                <dt className="text-gms-muted">{label}</dt>
                <dd className="mt-1 break-all text-gms-text">{value}</dd>
              </div>
            ))}
          </dl>
          {data.userContent && (
            <dl className="mt-8 space-y-6 text-sm">
              {[
                ["Conversation ID", data.userContent.conversation_id ?? "Not provided"],
                ["Input", data.userContent.input_text],
                ["Response", data.userContent.response_text ?? "No response recorded"]
              ].map(([label, value]) => (
                <div key={label} className="min-w-0">
                  <dt className="font-semibold text-gms-muted">{label}</dt>
                  <dd className="mt-2 whitespace-pre-wrap [overflow-wrap:anywhere] text-gms-text">{value}</dd>
                </div>
              ))}
            </dl>
          )}
          <h2 className="mt-10 text-xl font-bold text-gms-text">Execution Events</h2>
          {data.events.length === 0 ? (
            <p className="mt-4 text-sm text-gms-muted">No execution events recorded.</p>
          ) : (
            <ol className="mt-4 divide-y divide-gms-line">
              {data.events.map((event) => (
                <li key={event.sequence} className="grid gap-3 py-5 sm:grid-cols-[36px_1fr]">
                  <span className="font-semibold text-gms-blue">{event.sequence}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <span className="break-all font-mono text-sm text-gms-text">
                        {event.event}
                      </span>
                      <LogStatus value={event.outcome} />
                    </div>
                    <dl className="mt-3 grid gap-x-6 gap-y-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
                      {[
                        ["Time (UTC)", logTime(event.timestamp)],
                        ["Stage", event.stage.replaceAll("_", " ")],
                        ["Severity", event.severity],
                        ["Duration", logDuration(event.duration_ms)],
                        ["Tool", event.tool_name ?? "-"],
                        ["Reason code", event.reason_code ?? "-"]
                      ].map(([label, value]) => (
                        <div key={label} className="min-w-0">
                          <dt className="text-gms-muted">{label}</dt>
                          <dd className="mt-1 break-words text-gms-text">{value}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </>
      )}
    </LogsLayout>
  );
}
