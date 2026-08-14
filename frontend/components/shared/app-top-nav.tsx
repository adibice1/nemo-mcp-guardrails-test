"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import {
  getCurrentManagementUser,
  isAuthenticationError
} from "@/lib/api-client";
import {
  clearManagementSession,
  loadManagementSession,
  updateStoredManagementUser
} from "@/lib/management-auth";
import { cn } from "@/lib/utils";

type AppTopNavProps = {
  active?: "apps" | "policies" | "user-management" | "settings";
};

export function AppTopNav({ active }: AppTopNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const activeKey =
    active ??
    (pathname.startsWith("/apps")
      ? "apps"
      : pathname.startsWith("/user-management")
      ? "user-management"
      : pathname.startsWith("/settings")
      ? "settings"
      : "policies");

  useEffect(() => {
    const session = loadManagementSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    setIsAdmin(session.user.system_role === "admin");

    getCurrentManagementUser(session.access_token)
      .then((user) => {
        updateStoredManagementUser(user);
        setIsAdmin(user.system_role === "admin");
      })
      .catch((error) => {
        if (isAuthenticationError(error)) {
          clearManagementSession();
          router.replace("/login");
        }
      });
  }, [router]);

  return (
    <header className="mx-auto flex max-w-[1480px] items-center justify-between">
      <nav className="flex items-center gap-8 text-[21px] font-extrabold">
        <Link
          aria-label="Go to apps"
          className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#1187f6] text-3xl font-black text-[#1f3b9d] shadow-[0_8px_18px_rgba(17,135,246,0.22)]"
          href="/apps"
        >
          G
        </Link>
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
        {isAdmin && (
          <Link
            href="/user-management"
            className={cn(
              "relative pb-2 text-[#a8bcfb]",
              activeKey === "user-management" && "text-gms-blue"
            )}
          >
            User Management
            {activeKey === "user-management" && (
              <span className="absolute bottom-0 left-0 h-[4px] w-full rounded-full bg-gms-blue shadow-[0_4px_8px_rgba(71,117,255,0.55)]" />
            )}
          </Link>
        )}
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
      <Link
        aria-label="Open settings"
        className="h-11 w-11 overflow-hidden rounded-[13px] bg-[#ffc2d5] transition hover:scale-105"
        href="/settings"
      >
        <div className="flex h-full w-full items-end justify-center text-[30px]">
          <span aria-hidden="true">🙂</span>
        </div>
      </Link>
    </header>
  );
}
