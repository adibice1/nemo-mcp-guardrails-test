"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthIllustration } from "@/components/shared/auth-illustration";
import {
  getCurrentManagementUser,
  loginManagementUser
} from "@/lib/api-client";
import {
  clearManagementSession,
  loadManagementSession,
  saveManagementSession
} from "@/lib/management-auth";


export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const session = loadManagementSession();
    if (!session) return;

    getCurrentManagementUser(session.access_token)
      .then(() => router.replace("/apps"))
      .catch(() => clearManagementSession());
  }, [router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !password || submitting) return;

    setSubmitting(true);
    setError("");
    try {
      const session = await loginManagementUser(email.trim(), password);
      saveManagementSession(session, remember);
      router.push("/apps");
    } catch (loginError) {
      setError(
        loginError instanceof Error ? loginError.message : "Login failed."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-[#f8faff] dark:bg-[#17191f] lg:grid-cols-[1fr_1.1fr]">
      <section className="hidden items-center justify-center bg-[#eefaff] dark:bg-[#20242c] lg:flex">
        <AuthIllustration />
      </section>

      <section className="flex items-center justify-center px-6">
        <div className="w-full max-w-[370px]">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1187f6] text-4xl font-black text-[#1f3b9d]">
            G
          </div>
          <h1 className="mt-4 text-center text-2xl font-extrabold text-gms-text">
            Welcome Back!
          </h1>
          <p className="mt-2 text-center text-xs font-semibold text-gms-text">
            Login to your account
          </p>

          <div className="my-4 h-px bg-[#cfd6e6]" />

          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block text-xs font-bold text-gms-text">
              Enter Your Email
              <input
                autoComplete="email"
                className="mt-3 h-12 w-full rounded-md border border-[#d2d2d8] bg-white px-3 outline-none dark:border-gms-line dark:bg-[#252932]"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>

            <label className="block text-xs font-bold text-gms-text">
              Enter Your Password
              <input
                autoComplete="current-password"
                className="mt-3 h-12 w-full rounded-md border border-[#d2d2d8] bg-white px-3 outline-none dark:border-gms-line dark:bg-[#252932]"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>

            <div className="flex items-center text-xs font-semibold">
              <label className="flex items-center gap-2 text-gms-text">
                <input
                  checked={remember}
                  className="h-4 w-4"
                  type="checkbox"
                  onChange={(event) => setRemember(event.target.checked)}
                />
                Remember Me
              </label>
            </div>

            {error && (
              <p className="rounded-md bg-[#fff0f1] px-3 py-2 text-xs font-semibold text-gms-danger">
                {error}
              </p>
            )}

            <button
              className="flex h-12 w-full items-center justify-center rounded-full bg-[#138cf5] text-base font-extrabold text-white disabled:opacity-50"
              disabled={!email.trim() || !password || submitting}
              type="submit"
            >
              {submitting ? "Logging in..." : "Login"}
            </button>

            <p className="text-center text-xs font-semibold text-gms-muted">
              Need access? Ask your GMS administrator to create your account.
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}
