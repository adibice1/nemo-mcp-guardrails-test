"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

type AppTopNavProps = {
  active?: "apps" | "policies" | "settings";
};

export function AppTopNav({ active }: AppTopNavProps) {
  const pathname = usePathname();
  const activeKey =
    active ??
    (pathname.startsWith("/apps")
      ? "apps"
      : pathname.startsWith("/settings")
      ? "settings"
      : "policies");

  return (
    <header className="mx-auto flex max-w-[1480px] items-center justify-between">
      <nav className="flex items-center gap-8 text-[21px] font-extrabold">
        <Link
          href="/apps"
          className={cn(
            "relative pb-2 text-[#a8bcfb]",
            activeKey === "apps" && "text-gms-blue"
          )}
        >
          Apps
          {activeKey === "apps" && (
            <span className="absolute bottom-0 left-0 h-[4px] w-full rounded-full bg-gms-blue shadow-[0_4px_8px_rgba(71,117,255,0.55)]" />
          )}
        </Link>
        <Link
          href="/policies"
          className={cn(
            "relative pb-2 text-[#a8bcfb]",
            activeKey === "policies" && "text-gms-blue"
          )}
        >
          Policies
          {activeKey === "policies" && (
            <span className="absolute bottom-0 left-0 h-[4px] w-full rounded-full bg-gms-blue shadow-[0_4px_8px_rgba(71,117,255,0.55)]" />
          )}
        </Link>
        <Link
          href="/settings"
          className={cn(
            "relative pb-2 text-[#a8bcfb]",
            activeKey === "settings" && "text-gms-blue"
          )}
        >
          Settings
          {activeKey === "settings" && (
            <span className="absolute bottom-0 left-0 h-[4px] w-full rounded-full bg-gms-blue shadow-[0_4px_8px_rgba(71,117,255,0.55)]" />
          )}
        </Link>
      </nav>
      <div className="h-11 w-11 overflow-hidden rounded-[13px] bg-[#ffc2d5]">
        <div className="flex h-full w-full items-end justify-center text-[30px]">
          <span aria-hidden="true">🙂</span>
        </div>
      </div>
    </header>
  );
}
