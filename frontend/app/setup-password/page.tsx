"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PasswordChangeForm } from "@/components/settings/password-change-form";
import { getCurrentManagementUser } from "@/lib/api-client";
import { clearManagementSession, loadManagementSession } from "@/lib/management-auth";

export default function SetupPasswordPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    const session = loadManagementSession();
    if (!session) { router.replace("/login"); return; }
    let active = true;
    getCurrentManagementUser(session.access_token).then((user) => {
      if (!active) return;
      if (!user.must_change_password) { router.replace("/apps"); return; }
      setToken(session.access_token);
    }).catch(() => { if (active) setError("Session unavailable or expired. Sign in again or ask an administrator for a new temporary password."); });
    return () => { active = false; };
  }, [router]);
  return <main className="mx-auto max-w-xl space-y-4 p-8 text-gms-text">
    <h1 className="text-2xl font-bold">Choose your personal password</h1>
    <p>Replace your temporary password before using GMS. Enter it as the current password below.</p>
    {token && <PasswordChangeForm token={token} />}
    {error && <p role="alert">{error}</p>}
    <button type="button" onClick={() => { clearManagementSession(); router.replace("/login"); }}>Sign out</button>
  </main>;
}
