"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/discover", label: "Discovery" },
  { href: "/intelligence/seo", label: "SEO" },
  { href: "/intelligence/x", label: "X" },
  { href: "/intelligence/community", label: "Community" },
  { href: "/intelligence/competitors", label: "Competitors" },
  { href: "/intelligence/apps", label: "Apps" },
  { href: "/intelligence/youtube", label: "YouTube" },
  { href: "/reports", label: "Reports" },
  { href: "/saved", label: "Saved" },
  { href: "/validation", label: "Validation" },
  { href: "/outcomes", label: "Outcomes" },
  { href: "/integrations", label: "Integrations" },
  { href: "/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_#152033_0%,_#0b0f14_52%,_#080a0d_100%)] text-zinc-100">
      <div className="mx-auto flex min-h-screen max-w-7xl gap-0 md:gap-8 px-4 py-6 md:px-8">
        <aside className="hidden w-52 shrink-0 md:block">
          <Link href="/" className="block">
            <p className="text-xs uppercase tracking-[0.28em] text-teal-300/80">
              Opportunity intelligence
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">
              GUM
            </h1>
          </Link>
          <nav className="mt-8 space-y-1">
            {NAV.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-md px-3 py-2 text-sm transition ${
                    active
                      ? "bg-white/10 text-white"
                      : "text-zinc-400 hover:bg-white/5 hover:text-zinc-100"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="min-w-0 flex-1">
          <div className="mb-6 flex gap-2 overflow-x-auto pb-2 md:hidden">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="whitespace-nowrap rounded-md border border-white/10 px-3 py-1.5 text-xs text-zinc-300"
              >
                {item.label}
              </Link>
            ))}
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
