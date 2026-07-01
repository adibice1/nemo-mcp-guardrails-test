"use client";

import { Edit2, Folder, Globe2, MoreVertical, Trash2 } from "lucide-react";
import { FaMicrosoft } from "react-icons/fa6";
import { SiGithub } from "react-icons/si";
import { type PolicyRow } from "@/lib/mock-data";
import { cn, formatPolicyDate } from "@/lib/utils";

export type PolicySort = {
  key: "created" | "global";
  direction: "asc" | "desc";
};

type PolicyTableProps = {
  policies: PolicyRow[];
  page: number;
  pageSize: number;
  sort: PolicySort;
  totalCount: number;
  onDelete: (policy: PolicyRow) => void;
  onEdit: (policy: PolicyRow) => void;
  onOpen: (policy: PolicyRow) => void;
  onPageChange: (page: number) => void;
  onSort: (key: PolicySort["key"]) => void;
};

export function PolicyTable({
  policies,
  page,
  pageSize,
  sort,
  totalCount,
  onDelete,
  onEdit,
  onOpen,
  onPageChange,
  onSort
}: PolicyTableProps) {
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const startItem = totalCount === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalCount);

  return (
    <div className="mt-6">
      <div className="grid grid-cols-[46px_66px_180px_1fr_180px_150px_90px_94px_34px] items-center px-1 text-sm text-gms-muted">
        <span />
        <span />
        <span>Policy Connector</span>
        <span>Policy Name</span>
        <SortableHeader
          active={sort.key === "created"}
          direction={sort.direction}
          label="Created"
          onClick={() => onSort("created")}
        />
        <SortableHeader
          active={sort.key === "global"}
          direction={sort.direction}
          label="Global"
          onClick={() => onSort("global")}
        />
        <span>Edit</span>
        <span>Delete</span>
        <span />
      </div>

      <div className="mt-3 space-y-3">
        {policies.length > 0 ? (
          policies.map((policy, index) => (
            <PolicyRowItem
              key={policy.id}
              index={(page - 1) * pageSize + index + 1}
              policy={policy}
              onDelete={onDelete}
              onEdit={onEdit}
              onOpen={onOpen}
            />
          ))
        ) : (
          <div className="rounded-md border border-dashed border-gms-line bg-white py-12 text-center text-sm text-gms-muted dark:bg-[#20242c]">
            No policies found for this view.
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-center gap-4 text-sm text-gms-text">
        <span>
          Showing {startItem}-{endItem} of {totalCount}
        </span>
        <button
          className="text-gms-blue disabled:text-[#cbd5ee]"
          disabled={page <= 1}
          type="button"
          aria-label="Previous page"
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          &lsaquo;
        </button>
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gms-blue text-white">
          {page}
        </span>
        <button
          className="text-gms-blue disabled:text-[#cbd5ee]"
          disabled={page >= totalPages}
          type="button"
          aria-label="Next page"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        >
          &rsaquo;
        </button>
        <div className="flex items-center gap-2">
          <input
            aria-label="Go to page"
            className="w-10 border-b border-[#9eb3ff] bg-transparent pb-1 text-center text-gms-text outline-none"
            max={totalPages}
            min={1}
            type="number"
            value={page}
            onChange={(event) => {
              const nextPage = Number(event.target.value);
              if (!Number.isNaN(nextPage)) {
                onPageChange(Math.min(totalPages, Math.max(1, nextPage)));
              }
            }}
          />
          <span className="text-gms-muted">/ {totalPages}</span>
        </div>
      </div>
    </div>
  );
}

function SortableHeader({
  active,
  direction,
  label,
  onClick
}: {
  active: boolean;
  direction: PolicySort["direction"];
  label: string;
  onClick: () => void;
}) {
  const arrow = active ? (direction === "asc" ? "↑" : "↓") : "↕";

  return (
    <button
      className="inline-flex items-center gap-2 text-left transition hover:text-gms-blue"
      type="button"
      onClick={onClick}
    >
      {label}
      <span className={cn("text-xs text-[#91adff]", active && "text-gms-blue")}>
        {arrow}
      </span>
    </button>
  );
}

function PolicyRowItem({
  index,
  policy,
  onDelete,
  onEdit,
  onOpen
}: {
  index: number;
  policy: PolicyRow;
  onDelete: (policy: PolicyRow) => void;
  onEdit: (policy: PolicyRow) => void;
  onOpen: (policy: PolicyRow) => void;
}) {
  return (
    <div
      className="group grid min-h-[56px] cursor-pointer grid-cols-[46px_66px_180px_1fr_180px_150px_90px_94px_34px] items-center rounded-md border border-gms-line bg-white px-1 text-sm text-gms-text shadow-[0_1px_2px_rgba(55,70,110,0.04)] transition hover:border-gms-blue hover:bg-gms-blue hover:text-white dark:bg-[#20242c]"
      role="button"
      tabIndex={0}
      onClick={() => onOpen(policy)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onOpen(policy);
        }
      }}
    >
      <span className="text-center text-xl font-extrabold text-[#a7bcf8] group-hover:text-white">
        {index}
      </span>
      <span className="flex justify-center">
        <ConnectorIcon connector={policy.connector} global={policy.global} />
      </span>
      <span className="font-medium text-gms-blue group-hover:text-white">
        {policy.connector}
      </span>
      <span>{policy.name}</span>
      <span>{formatPolicyDate(policy.created)}</span>
      <span>
        {policy.global && (
          <span className="inline-flex h-9 min-w-[88px] items-center justify-center rounded-md bg-gms-blue px-5 text-white shadow-button group-hover:bg-white group-hover:text-gms-blue">
            Global
          </span>
        )}
      </span>
      <span>
        <button
          className="flex h-8 w-8 items-center justify-center rounded-full bg-gms-blue-soft text-gms-blue group-hover:bg-[#c8d7ff] group-hover:text-[#2f63e8]"
          type="button"
          aria-label={`Edit ${policy.name}`}
          onClick={(event) => {
            event.stopPropagation();
            onEdit(policy);
          }}
        >
          <Edit2 className="h-4 w-4" />
        </button>
      </span>
      <span>
        <button
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-full bg-[#fff0f1] text-gms-danger",
            "group-hover:bg-[#ffd2d9] group-hover:text-[#e33b52]"
          )}
          type="button"
          aria-label={`Delete ${policy.name}`}
          onClick={(event) => {
            event.stopPropagation();
            onDelete(policy);
          }}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </span>
      <button
        className="text-[#d7deea] group-hover:text-white"
        type="button"
        aria-label={`More actions for ${policy.name}`}
        onClick={(event) => event.stopPropagation()}
      >
        <MoreVertical className="h-6 w-6" />
      </button>
    </div>
  );
}

function ConnectorIcon({
  connector,
  global
}: {
  connector: string;
  global: boolean;
}) {
  if (global) {
    return (
      <Globe2 className="h-8 w-8 text-gms-blue transition-colors group-hover:text-white" />
    );
  }

  const connectorKey = connector.trim().toLowerCase();

  if (connectorKey === "github") {
    return (
      <SiGithub className="h-8 w-8 text-[#24292f] transition-colors group-hover:text-white dark:text-white" />
    );
  }

  if (connectorKey === "sharepoint") {
    return (
      <FaMicrosoft
        aria-label="SharePoint"
        className="h-8 w-8 text-[#038387] transition-colors group-hover:text-white"
      />
    );
  }

  return (
    <Folder className="h-8 w-8 fill-[#e3eefc] text-[#4791ff] group-hover:fill-white group-hover:text-white" />
  );
}
