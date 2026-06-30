import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Guardrails Management System",
  description: "Frontend prototype for managing GitHub MCP guardrail policies"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (localStorage.getItem("gms:theme") === "dark") {
                  document.documentElement.classList.add("dark");
                }
              } catch (_) {}
            `
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
