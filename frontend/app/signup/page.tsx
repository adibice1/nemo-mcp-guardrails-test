import Link from "next/link";
import { AuthIllustration } from "@/components/shared/auth-illustration";

export default function SignupPage() {
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

          <form className="mt-12 space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FloatingInput label="First Name" placeholder="John" />
              <FloatingInput label="Last Name" placeholder="Doe" />
              <FloatingInput label="Email" placeholder="john.doe@gmail.com" />
              <FloatingInput label="Phone Number" placeholder="+00 0000 000 00 00" />
            </div>
            <FloatingInput label="Password" placeholder="••••••••••••••••••••" type="password" />
            <FloatingInput
              label="Confirm Password"
              placeholder="••••••••••••••••••••"
              type="password"
            />

            <label className="flex items-center gap-3 text-xl text-black dark:text-gms-text">
              <input className="h-5 w-5" type="checkbox" />
              <span>
                I agree to all the{" "}
                <a className="text-[#1c53ff]" href="#">
                  Terms
                </a>{" "}
                and{" "}
                <a className="text-[#1c53ff]" href="#">
                  Privacy Policies
                </a>
              </span>
            </label>

            <Link
              className="mt-12 flex h-14 w-full items-center justify-center rounded bg-gms-blue text-2xl font-medium text-white"
              href="/policies"
            >
              Next
            </Link>
          </form>
        </div>
      </section>
    </main>
  );
}

function FloatingInput({
  label,
  placeholder,
  type = "text"
}: {
  label: string;
  placeholder: string;
  type?: string;
}) {
  return (
    <label className="relative block">
      <span className="absolute -top-2 left-4 bg-white px-1 text-sm text-black dark:bg-[#17191f] dark:text-gms-text">
        {label}
      </span>
      <input
        className="h-14 w-full rounded border border-[#4e4e4e] bg-white px-4 text-lg text-gms-text outline-none placeholder:text-[#8a8a8a] dark:border-gms-line dark:bg-[#252932]"
        placeholder={placeholder}
        type={type}
      />
    </label>
  );
}
