"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { changeManagementPassword } from "@/lib/api-client";
import { clearManagementSession } from "@/lib/management-auth";

export function PasswordChangeForm({ token }: { token: string }) {
  const router = useRouter();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !token) return;
    setError("");
    if (newPassword !== confirmation) {
      setError("New passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await changeManagementPassword(token, currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmation("");
      clearManagementSession();
      router.replace("/login?passwordChanged=1");
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Could not change password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-xl border border-gms-line p-4">
      <h2 className="text-lg font-extrabold text-gms-text">Change password</h2>
      <p className="text-sm text-gms-muted">
        Use 15–256 characters. A memorable passphrase is welcome.
        After changing your password, sign in again.
      </p>
      {[
        { label: "Current password", value: currentPassword, change: setCurrentPassword,
          autoComplete: "current-password", minLength: 1 },
        { label: "New password", value: newPassword, change: setNewPassword,
          autoComplete: "new-password", minLength: 15 },
        { label: "Confirm new password", value: confirmation, change: setConfirmation,
          autoComplete: "new-password", minLength: 15 }
      ].map((field) => (
        <label key={field.label} className="block text-sm font-semibold text-gms-text">
          {field.label}
          <input type="password" required minLength={field.minLength} maxLength={256}
            autoComplete={field.autoComplete} value={field.value} disabled={busy}
            onChange={(event) => field.change(event.target.value)}
            className="mt-1 block w-full rounded-lg border border-gms-line bg-white p-3 dark:bg-[#252932]" />
        </label>
      ))}
      {error && <p role="alert" className="text-sm text-gms-danger">{error}</p>}
      <button type="submit" disabled={busy || !token}
        className="rounded-lg bg-gms-blue px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
        {busy ? "Changing..." : "Change password"}
      </button>
    </form>
  );
}
