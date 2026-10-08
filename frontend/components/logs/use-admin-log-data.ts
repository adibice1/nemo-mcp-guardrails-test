"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiRequestError, isAuthenticationError } from "@/lib/api-client";
import { loadManagementSession } from "@/lib/management-auth";

type Loader<T> = (signal: AbortSignal) => Promise<T>;
type Result<T> = {
  load: Loader<T>;
  version: number;
  data: T | null;
  error: string;
};

export function useAdminLogData<T>(load: Loader<T>) {
  const router = useRouter();
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<Result<T> | null>(null);
  const retry = useCallback(() => setVersion((value) => value + 1), []);

  useEffect(() => {
    function handleStorage(event: StorageEvent) {
      if (event.key === null || event.key === "gms:management-session") {
        retry();
      }
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [retry]);

  useEffect(() => {
    const session = loadManagementSession();
    const finish = (data: T | null, error = "") => {
      setResult({ load, version, data, error });
    };
    if (!session) {
      finish(null, "Authentication required.");
      router.replace("/login");
      return;
    }
    if (session.user.system_role !== "admin") {
      finish(null, "Administrator access required.");
      return;
    }

    const token = session.access_token;
    const controller = new AbortController();
    load(controller.signal)
      .then((data) => {
        if (
          !controller.signal.aborted &&
          loadManagementSession()?.access_token === token
        ) finish(data);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const current = loadManagementSession();
        if (current && current.access_token !== token) return;
        if (isAuthenticationError(error)) router.replace("/login");
        finish(
          null,
          error instanceof ApiRequestError && error.status === 403
            ? "Administrator access required."
            : error instanceof Error
            ? error.message
            : "Could not load runtime logs."
        );
      });
    return () => controller.abort();
  }, [load, version, router]);

  const current =
    result?.load === load && result.version === version ? result : null;
  return {
    data: current?.data ?? null,
    error: current?.error ?? "",
    loading: current === null,
    retry
  };
}
