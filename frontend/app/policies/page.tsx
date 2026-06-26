"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Plus, Search } from "lucide-react";
import { CreatePolicyModal } from "@/components/policies/create-policy-modal";
import { PolicyTable, type PolicySort } from "@/components/policies/policy-table";
import { AppTopNav } from "@/components/shared/app-top-nav";
import { appOptions, initialPolicies, type PolicyRow } from "@/lib/mock-data";

const SELECTED_APP_STORAGE_KEY = "gms:selected-app";
const PAGE_SIZE = 8;

export default function PoliciesPage() {
  const [selectedApp, setSelectedApp] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [policies, setPolicies] = useState<PolicyRow[]>(initialPolicies);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<PolicySort>({
    key: "created",
    direction: "desc"
  });

  useEffect(() => {
    const savedApp = window.localStorage.getItem(SELECTED_APP_STORAGE_KEY);
    if (savedApp !== null) {
      setSelectedApp(savedApp);
    }
  }, []);

  function handleSelectedAppChange(value: string) {
    setSelectedApp(value);
    setPage(1);
    window.localStorage.setItem(SELECTED_APP_STORAGE_KEY, value);
  }

  function handleSort(nextKey: PolicySort["key"]) {
    setSort((current) => ({
      key: nextKey,
      direction:
        current.key === nextKey && current.direction === "desc" ? "asc" : "desc"
    }));
    setPage(1);
  }

  const visiblePolicies = useMemo(() => {
    const scoped = selectedApp
      ? policies.filter((policy) => policy.global || policy.app === selectedApp)
      : policies.filter((policy) => policy.global);

    const filtered = search.trim()
      ? scoped.filter((policy) => {
          const needle = search.trim().toLowerCase();
          return (
            policy.name.toLowerCase().includes(needle) ||
            policy.connector.toLowerCase().includes(needle)
          );
        })
      : scoped;

    return [...filtered].sort((first, second) => {
      if (sort.key === "global") {
        const firstValue = first.global ? 1 : 0;
        const secondValue = second.global ? 1 : 0;
        return sort.direction === "asc"
          ? firstValue - secondValue
          : secondValue - firstValue;
      }

      const firstTime = new Date(first.created).getTime();
      const secondTime = new Date(second.created).getTime();
      return sort.direction === "asc"
        ? firstTime - secondTime
        : secondTime - firstTime;
    });
  }, [policies, search, selectedApp, sort]);

  const totalPages = Math.max(1, Math.ceil(visiblePolicies.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginatedPolicies = visiblePolicies.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE
  );

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="policies" />

      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-8 py-12 shadow-shell lg:px-20">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="text-4xl font-extrabold tracking-normal text-gms-text lg:text-[42px]">
              Guardrails Management System
            </h1>

            <div className="relative mt-12 w-[210px]">
              <label className="text-xs font-semibold uppercase tracking-wide text-gms-text">
                Apps
              </label>
              <select
                className="mt-2 h-9 w-full appearance-none border-b border-gms-line bg-transparent pr-8 text-sm text-gms-text outline-none"
                value={selectedApp}
                onChange={(event) => handleSelectedAppChange(event.target.value)}
              >
                <option value="">Global policies</option>
                {appOptions.map((app) => (
                  <option key={app} value={app}>
                    {app}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute bottom-2 right-2 h-4 w-4 text-[#c0c8d7]" />
            </div>
          </div>

          <div className="flex flex-col items-stretch gap-9 lg:items-end">
            <label className="relative block w-full lg:w-[405px]">
              <input
                className="h-11 w-full rounded-xl border border-gms-line bg-white px-4 pr-11 text-sm text-gms-text shadow-field outline-none placeholder:text-gms-muted"
                placeholder="Search"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
              />
              <Search className="absolute right-5 top-3 h-5 w-5 text-gms-text" />
            </label>

            <button
              className="inline-flex h-10 items-center justify-center gap-3 rounded-md bg-gms-blue px-4 text-sm font-medium text-white shadow-button"
              type="button"
              onClick={() => setModalOpen(true)}
            >
              <Plus className="h-5 w-5" />
              Create Policy
            </button>
          </div>
        </div>

        <PolicyTable
          page={safePage}
          pageSize={PAGE_SIZE}
          policies={paginatedPolicies}
          sort={sort}
          totalCount={visiblePolicies.length}
          onPageChange={setPage}
          onSort={handleSort}
        />
      </section>

      <CreatePolicyModal
        appName={selectedApp || null}
        isAdmin
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={(policy) => {
          setPolicies((current) => [policy, ...current]);
          setModalOpen(false);
        }}
      />
    </main>
  );
}
