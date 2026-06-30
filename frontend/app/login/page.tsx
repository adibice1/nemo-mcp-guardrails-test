import Link from "next/link";
import { AuthIllustration } from "@/components/shared/auth-illustration";

export default function LoginPage() {
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

          <form className="space-y-4">
            <label className="block text-xs font-bold text-gms-text">
              Enter Your Email
              <input className="mt-3 h-12 w-full rounded-md border border-[#d2d2d8] bg-white px-3 outline-none dark:border-gms-line dark:bg-[#252932]" />
            </label>

            <label className="block text-xs font-bold text-gms-text">
              Enter Your Password
              <input
                className="mt-3 h-12 w-full rounded-md border border-[#d2d2d8] bg-white px-3 outline-none dark:border-gms-line dark:bg-[#252932]"
                type="password"
              />
            </label>

            <div className="flex items-center justify-between text-xs font-semibold">
              <label className="flex items-center gap-2 text-gms-text">
                <input className="h-4 w-4" type="checkbox" />
                Remember Me
              </label>
              <a className="text-[#322b8f]" href="#">
                Recover Password
              </a>
            </div>

            <Link
              className="flex h-12 w-full items-center justify-center rounded-full bg-[#138cf5] text-base font-extrabold text-white"
              href="/policies"
            >
              Login
            </Link>

            <p className="text-center text-xs font-semibold">
              Don&apos;t have an account?{" "}
              <Link className="text-[#138cf5]" href="/signup">
                Register Now!
              </Link>
            </p>
          </form>
        </div>
      </section>
    </main>
  );
}
