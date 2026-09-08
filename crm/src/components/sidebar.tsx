"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Дашборд" },
  { href: "/leads", label: "Заявки" },
  { href: "/instructor", label: "К инструктору" },
  { href: "/gym", label: "Общий зал" },
  { href: "/clients", label: "Клиенты" },
];

export function Sidebar({
  userEmail,
  signOut,
}: {
  userEmail: string | null;
  signOut: () => Promise<void>;
}) {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)] px-3 py-4">
      <div className="px-2 pb-4">
        <div className="text-sm font-semibold tracking-tight">ХанБио CRM</div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5">
        {NAV.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-lg px-2.5 py-2 text-sm transition-colors ${
                active
                  ? "bg-[var(--accent-soft)] font-medium text-[var(--accent)]"
                  : "text-[var(--text-muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[var(--border)] pt-3">
        <div className="truncate px-2 text-xs text-[var(--text-muted)]">
          {userEmail ?? "—"}
        </div>
        <form action={signOut}>
          <button
            type="submit"
            className="mt-1.5 w-full rounded-lg px-2.5 py-1.5 text-left text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          >
            Выйти
          </button>
        </form>
      </div>
    </aside>
  );
}
