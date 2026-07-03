"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthIllustration } from "@/components/shared/auth-illustration";
import { signupManagementUser } from "@/lib/api-client";
import { saveManagementSession } from "@/lib/management-auth";


export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 12) {
      setError("Password must contain at least 12 characters.");
      return;
    }
    if (!acceptedTerms || submitting) return;

    setSubmitting(true);
    setError("");
    try {
      const session = await signupManagementUser(email.trim(), password);
      saveManagementSession(session, true);
      router.push("/apps");
    } catch (signupError) {
      setError(
        signupError instanceof Error ? signupError.message : "Registration failed."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-white dark:bg-[#17191f] lg:grid-cols-[1fr_1.1fr]">
      <section className="hidden items-center justify-center bg-[#eefaff] dark:bg-[#20242c] lg:flex">
        <AuthIllustration />
      </section>

      <section className="flex items-center justify-center px-6">
        <div className="w-full max-w-[650px]">
          <h1 className="text-[42px] font-black leading-tight text-black dark:text-gms-text">
            Register an account for the
            <br />
            <span className="text-[#138cf5]">
              Guardrail Management System
            </span>
          </h1>

          <form className="mt-12 space-y-4" onSubmit={handleSubmit}>
            <FloatingInput
              autoComplete="email"
              label="Email"
              placeholder="john.doe@gmail.com"
              type="email"
              value={email}
              onChange={setEmail}
            />
            <FloatingInput
              autoComplete="new-password"
              label="Password"
              placeholder="At least 12 characters"
              type="password"
              value={password}
              onChange={setPassword}
            />
            <FloatingInput
              autoComplete="new-password"
              label="Confirm Password"
              placeholder="Repeat your password"
              type="password"
              value={confirmPassword}
              onChange={setConfirmPassword}
            />

            <label className="flex items-center gap-3 text-base text-black dark:text-gms-text">
              <input
                checked={acceptedTerms}
                className="h-5 w-5"
                type="checkbox"
                onChange={(event) => setAcceptedTerms(event.target.checked)}
              />
              <span>I agree to the Terms and Privacy Policies</span>
            </label>

            {error && (
              <p className="rounded-md bg-[#fff0f1] px-3 py-2 text-sm font-semibold text-gms-danger">
                {error}
              </p>
            )}

            <button
              className="mt-8 flex h-14 w-full items-center justify-center rounded bg-gms-blue text-xl font-medium text-white disabled:opacity-50"
              disabled={
                !email.trim() ||
                !password ||
                !confirmPassword ||
                !acceptedTerms ||
                submitting
              }
              type="submit"
            >
              {submitting ? "Creating account..." : "Create Account"}
            </button>

            <p className="text-center text-sm text-gms-muted">
              Already registered?{" "}
              <Link className="font-semibold text-gms-blue" href="/login">
                Login
              </Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}


function FloatingInput({
  autoComplete,
  label,
  placeholder,
  type,
  value,
  onChange
}: {
  autoComplete: string;
  label: string;
  placeholder: string;
  type: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="relative block">
      <span className="absolute -top-2 left-4 bg-white px-1 text-sm text-black dark:bg-[#17191f] dark:text-gms-text">
        {label}
      </span>
      <input
        autoComplete={autoComplete}
        className="h-14 w-full rounded border border-[#4e4e4e] bg-white px-4 text-lg text-gms-text outline-none placeholder:text-[#8a8a8a] dark:border-gms-line dark:bg-[#252932]"
        placeholder={placeholder}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
