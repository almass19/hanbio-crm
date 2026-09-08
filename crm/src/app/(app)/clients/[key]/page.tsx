import Link from "next/link";
import { notFound } from "next/navigation";
import { getClientDetail } from "@/lib/queries";
import { fmtDate, fmtDateTime, fmtPhone } from "@/lib/format";
import { scenarioLabel } from "@/lib/types";
import { Badge, Card, PageHeader } from "@/components/ui";

export const dynamic = "force-dynamic";

type Item =
  | { kind: "request"; at: string; title: string; sub: string; tone: "warn" | "ok" }
  | { kind: "gym"; at: string; title: string; sub: string }
  | { kind: "instructor"; at: string; title: string; sub: string; tone: "warn" | "ok" };

export default async function ClientPage({
  params,
}: {
  params: Promise<{ key: string }>;
}) {
  const { key } = await params;
  const client = await getClientDetail(decodeURIComponent(key));
  if (!client) notFound();

  const items: Item[] = [
    ...client.requests.map(
      (r): Item => ({
        kind: "request",
        at: r.created_at,
        title: scenarioLabel(r.scenario_key),
        sub: r.admin_comment ? `Комментарий: ${r.admin_comment}` : "",
        tone: r.status === "processed" ? "ok" : "warn",
      }),
    ),
    ...client.gym.map(
      (b): Item => ({
        kind: "gym",
        at: b.created_at,
        title: `Общий зал · ${fmtDate(b.session_date)} ${b.session_time} · аппарат ${b.seat_number}`,
        sub: "",
      }),
    ),
    ...client.instructor.map(
      (b): Item => ({
        kind: "instructor",
        at: b.created_at,
        title: `Инструктор · ${fmtDate(b.session_date)} ${b.session_time}`,
        sub: [b.instructor, b.programs_comment].filter(Boolean).join(" · "),
        tone: b.status === "Обработан" ? "ok" : "warn",
      }),
    ),
  ].sort((a, b) => b.at.localeCompare(a.at));

  const KIND_LABEL = {
    request: "Заявка",
    gym: "Зал",
    instructor: "Инструктор",
  } as const;

  return (
    <>
      <PageHeader
        title={client.name}
        subtitle={fmtPhone(client.phone)}
        actions={
          <Link
            href="/clients"
            className="text-sm text-[var(--accent)] hover:underline"
          >
            ← К списку
          </Link>
        }
      />

      <div className="grid grid-cols-3 gap-3">
        <Card>
          <div className="p-4">
            <div className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Заявок
            </div>
            <div className="mt-1 text-2xl font-semibold tabular-nums">
              {client.requests.length}
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              Записей в зал
            </div>
            <div className="mt-1 text-2xl font-semibold tabular-nums">
              {client.gym.length}
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-4">
            <div className="text-xs uppercase tracking-wide text-[var(--text-muted)]">
              К инструктору
            </div>
            <div className="mt-1 text-2xl font-semibold tabular-nums">
              {client.instructor.length}
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="border-b border-[var(--border)] px-4 py-3">
          <h2 className="text-sm font-semibold">История</h2>
        </div>
        <ul className="divide-y divide-[var(--border)]">
          {items.map((it, i) => (
            <li key={i} className="flex gap-3 px-4 py-3">
              <div className="w-36 shrink-0 text-xs text-[var(--text-muted)] tabular-nums">
                {fmtDateTime(it.at)}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Badge tone="neutral">{KIND_LABEL[it.kind]}</Badge>
                  {"tone" in it && it.tone && (
                    <Badge tone={it.tone}>
                      {it.tone === "ok" ? "обработано" : "в работе"}
                    </Badge>
                  )}
                </div>
                <div className="mt-1 text-sm">{it.title}</div>
                {it.sub && (
                  <div className="mt-0.5 text-xs text-[var(--text-muted)]">
                    {it.sub}
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}
