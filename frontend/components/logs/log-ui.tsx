"use client";

import { type PropsWithChildren } from "react";
import { AppTopNav } from "@/components/shared/app-top-nav";
import { cn } from "@/lib/utils";

export function LogsLayout({
  title,
  children
}: PropsWithChildren<{ title: string }>) {
  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="logs" />
      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-8 py-12 shadow-shell dark:bg-[#1b1e25] lg:px-20">
        <h1 className="break-words text-4xl font-extrabold tracking-normal text-gms-text lg:text-[42px]">
          {title}
        </h1>
        {children}
      </section>
    </main>
  );
}

export function LogStatus({ value }: { value: string }) {
  const blocked = ["blocked", "error", "tool_error", "rejected"].includes(value);
  const warning = ["raised", "modified", "truncated"].includes(value);
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center rounded-md px-2 py-1 text-xs font-semibold capitalize",
        "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200",
        value === "passed" &&
          "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200",
        blocked &&
          "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
        warning &&
          "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200"
      )}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function logTime(value: string | null) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Invalid timestamp"
    : date.toISOString().replace("T", " ").replace("Z", "");
}

export function logDuration(value: number | null) {
  return value === null ? "-" : `${value.toFixed(1)} ms`;
}
