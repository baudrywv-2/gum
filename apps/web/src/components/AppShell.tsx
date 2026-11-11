"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = { href: string; label: string; primary?: boolean };

const NAV_GROUPS: { title: string; items: NavItem[] }[] = [
  {
    title: "Workspace",
    items: [
      { href: "/", label: "Overview" },
      { href: "/discover", label: "Discovery", primary: true },
      { href: "/reports", label: "Reports" },
      { href: "/saved", label: "Saved" },
    ],
  },
  {
    title: "Sources",
    items: [
      { href: "/intelligence/seo", label: "SEO" },
      { href: "/intelligence/x", label: "X" },
      { href: "/intelligence/community", label: "Community" },
      { href: "/intelligence/competitors", label: "Competitors" },
      { href: "/intelligence/apps", label: "Apps" },
      { href: "/intelligence/youtube", label: "YouTube" },
    ],
  },
  {
    title: "Operations",
    items: [
      { href: "/validation", label: "Validation" },
      { href: "/outcomes", label: "Outcomes" },
      { href: "/integrations", label: "Integrations" },
      { href: "/settings", label: "Settings" },
    ],
  },
];

const FLAT_NAV = NAV_GROUPS.flatMap((g) => g.items);

function isActive(pathname: string, href: string) {
  return href === "/"
    ? pathname === "/"
    : pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="gum-atmosphere ambient-shift min-h-screen text-ink">
      <div className="gum-shell mx-auto flex min-h-screen max-w-7xl gap-0 px-4 py-5 md:gap-10 md:px-8 md:py-8">
        <aside className="hidden w-56 shrink-0 md:flex md:flex-col">
          <Link href="/" className="group block anim-fade">
            <p className="text-[10px] font-medium uppercase tracking-[0.28em] text-signal">
              Opportunity intelligence
            </p>
            <h1 className="mt-1 font-display text-5xl font-medium tracking-tight text-ink transition group-hover:text-signal">
              GUM
            </h1>
          </Link>

          <nav className="mt-10 flex-1 space-y-7">
            {NAV_GROUPS.map((group) => (
              <div key={group.title}>
                <p className="mb-2 px-3 text-[10px] font-medium uppercase tracking-[0.18em] text-muted/80">
                  {group.title}
                </p>
                <ul className="space-y-0.5">
                  {group.items.map((item) => {
                    const active = isActive(pathname, item.href);
                    return (
                      <li key={item.href}>
                        <Link
                          href={item.href}
                          className={`relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition ${
                            active
                              ? "bg-white/75 font-medium text-ink shadow-soft"
                              : "text-ink-soft hover:bg-white/45 hover:text-ink"
                          } ${item.primary && !active ? "font-medium text-signal" : ""}`}
                        >
                          {active && (
                            <span
                              aria-hidden
                              className="absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-r bg-signal"
                            />
                          )}
                          {item.label}
                          {item.primary && (
                            <span className="ml-auto text-[10px] uppercase tracking-wider text-signal/80">
                              Main
                            </span>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>

          <p className="mt-6 px-3 text-[11px] leading-relaxed text-muted/70">
            Evidence-first scores. Claims stay labeled.
          </p>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="mb-5 flex items-center justify-between gap-3 md:hidden">
            <Link href="/" className="min-w-0">
              <p className="text-[10px] uppercase tracking-[0.22em] text-signal">
                Opportunity intelligence
              </p>
              <p className="font-display text-3xl font-medium leading-none text-ink">
                GUM
              </p>
            </Link>
            <Link href="/discover" className="btn-primary shrink-0 px-3.5 py-2 text-xs">
              Discover
            </Link>
          </header>

          <div className="-mx-1 mb-6 flex gap-1.5 overflow-x-auto px-1 pb-1 md:hidden">
            {FLAT_NAV.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`whitespace-nowrap rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                    active
                      ? "border-signal bg-signal text-white shadow-soft"
                      : "border-line bg-white/55 text-ink-soft"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>

          <div className="anim-rise">{children}</div>
        </div>
      </div>
    </div>
  );
}
