"use client";

import Link from "next/link";
import { AuthIllustration } from "@/components/shared/auth-illustration";


export default function SignupPage() {
  return (
    <main className="grid min-h-screen bg-white dark:bg-[#17191f] lg:grid-cols-[1fr_1.1fr]">
      <section className="hidden items-center justify-center bg-[#eefaff] dark:bg-[#20242c] lg:flex">
        <AuthIllustration />
      </section>

      <section className="flex items-center justify-center px-6">
        <div className="w-full max-w-[620px]">
          <h1 className="text-[42px] font-black leading-tight text-black dark:text-gms-text">
            Account registration is
            <br />
            <span className="text-[#138cf5]">admin managed</span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-gms-muted">
            GMS accounts are created by administrators. Ask your administrator
            for your login email and temporary password, then sign in and update
            your profile from Settings.
          </p>
          <Link
            className="mt-8 inline-flex h-12 items-center justify-center rounded-full bg-[#138cf5] px-8 text-base font-extrabold text-white"
            href="/login"
          >
            Back to Login
          </Link>
        </div>
      </section>
    </main>
  );
}
