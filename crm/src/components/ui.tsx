import { type ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 border-b border-[var(--border)] pb-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="mt-0.5 text-sm text-[var(--text-muted)]">{subtitle}</p>
        )}
      </div>
      {actions}
    </div>
  );
}

type Tone = "ok" | "warn" | "info" | "neutral";

const TONE: Record<Tone, string> = {
  ok: "bg-[var(--ok-bg)] text-[var(--ok-fg)]",
  warn: "bg-[var(--warn-bg)] text-[var(--warn-fg)]",
  info: "bg-[var(--info-bg)] text-[var(--info-fg)]",
  neutral: "bg-[var(--surface-2)] text-[var(--text-muted)]",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${TONE[tone]}`}
    >
      {children}
    </span>
  );
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
        {label}
      </div>
      <div className="mt-1.5 text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-[var(--text-muted)]">{hint}</div>}
    </div>
  );
}

export function Card({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)]">
      {children}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="px-4 py-16 text-center text-sm text-[var(--text-muted)]">
      {children}
    </div>
  );
}

export function Th({ children }: { children: ReactNode }) {
  return (
    <th className="whitespace-nowrap px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
      {children}
    </th>
  );
}

export function Td({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <td className={`px-3 py-2.5 align-top text-sm ${className}`}>{children}</td>
  );
}

export function DemoNotice() {
  return (
    <div className="rounded-xl border border-[var(--info-fg)]/25 bg-[var(--info-bg)] px-4 py-3 text-sm text-[var(--info-fg)]">
      <span className="font-medium">Демо-режим.</span> Показаны примерные данные —
      Supabase ещё не подключён. Подключите его по{" "}
      <code>crm/README.md</code>, чтобы работать с настоящими заявками и записями.
    </div>
  );
}

export function supabaseConfigured(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  );
}
