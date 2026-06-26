import { SettingsForm } from "@/components/settings/settings-form";
import { AppTopNav } from "@/components/shared/app-top-nav";

export default function SettingsPage() {
  return (
    <main className="min-h-screen bg-gms-bg px-6 py-8 lg:px-20">
      <AppTopNav active="settings" />
      <section className="mx-auto mt-4 min-h-[calc(100vh-112px)] max-w-[1480px] rounded-[24px] bg-white px-14 py-9 shadow-shell lg:px-16">
        <SettingsForm />
      </section>
    </main>
  );
}
