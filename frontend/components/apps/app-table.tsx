"use client";

import { Bot, ChevronRight, Trash2 } from "lucide-react";
import { type ClientApp } from "@/lib/api-client";
import { formatPolicyDate } from "@/lib/utils";

export type AppSummary = ClientApp & {
  connectorCount: number;
  policyCount: number;
};

type AppTableProps = {
  apps: AppSummary[];
  page: number;
  pageSize: number;
  totalCount: number;
  onDelete: (app: AppSummary) => void;
  onOpen: (app: AppSummary) => void;
  onPageChange: (page: number) => void;
};

export function AppTable({
  apps,
  page,
  pageSize,
  totalCount,
  onDelete,
  onOpen,
  onPageChange
}: AppTableProps) {
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const startItem = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalCount);

  return (
    <div className="mt-8 overflow-x-auto">
      <div className="min-w-[820px]">
        <div className="grid grid-cols-[54px_64px_1.8fr_120px_120px_180px_70px_40px] items-center px-1 text-sm text-gms-muted">
          <span />
          <span />
          <span>Application Name</span>
          <span>Connectors</span>
          <span>Policies</span>
          <span>Created</span>
          <span>Delete</span>
          <span />
        </div>

        <div className="mt-3 space-y-3">
          {apps.length > 0 ? (
            apps.map((app, index) => (
              <div
                key={app.id}
                className="group grid min-h-[62px] w-full cursor-pointer grid-cols-[54px_64px_1.8fr_120px_120px_180px_70px_40px] items-center rounded-md border border-gms-line bg-white px-1 text-left text-sm text-gms-text transition hover:border-gms-blue hover:bg-gms-blue hover:text-white dark:bg-[#20242c]"
                role="button"
                tabIndex={0}
                onClick={() => onOpen(app)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    onOpen(app);
                  }
                }}
              >
                <span className="text-center text-xl font-extrabold text-[#a7bcf8] group-hover:text-white">
                  {(page - 1) * pageSize + index + 1}
                </span>
                <span className="flex justify-center">
                  <span className="flex h-9 w-9 items-center justify-center rounded-md bg-gms-blue-soft text-gms-blue group-hover:bg-white group-hover:text-gms-blue">
                    <Bot className="h-5 w-5" />
                  </span>
                </span>
                <span className="font-semibold">{app.name}</span>
                <span>{app.connectorCount}</span>
                <span>{app.policyCount}</span>
                <span>{formatPolicyDate(app.created_at)}</span>
                <span>
                  <button
                    aria-label={`Delete ${app.name}`}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-[#fff0f1] text-gms-danger group-hover:bg-[#ffd2d9] group-hover:text-[#e33b52]"
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onDelete(app);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </span>
                <ChevronRight className="h-5 w-5 text-[#c4cce0] group-hover:text-white" />
              </div>
            ))
          ) : (
            <div className="rounded-md border border-dashed border-gms-line bg-white py-14 text-center text-sm text-gms-muted dark:bg-[#20242c]">
              No applications found.
            </div>
          )}
        </div>

        <div className="mt-5 flex items-center justify-center gap-4 text-sm text-gms-text">
          <span>
            Showing {startItem}-{endItem} of {totalCount}
          </span>
          <button
            className="text-gms-blue disabled:text-[#cbd5ee]"
            disabled={page <= 1}
            type="button"
            onClick={() => onPageChange(Math.max(1, page - 1))}
          >
            &lsaquo;
          </button>
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gms-blue text-white">
            {page}
          </span>
          <span className="text-gms-muted">/ {totalPages}</span>
          <button
            className="text-gms-blue disabled:text-[#cbd5ee]"
            disabled={page >= totalPages}
            type="button"
            onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          >
            &rsaquo;
          </button>
        </div>
      </div>
    </div>
  );
}
