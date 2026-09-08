import Link from "next/link";
import { getRequests, isDemo } from "@/lib/queries";
import { Card, DemoNotice, EmptyState, PageHeader, Th } from "@/components/ui";
import { LeadRow } from "./lead-row";

export const dynamic = "force-dynamic";

const TABS = [
  { key: "new", label: "Новые" },
  { key: "processed", label: "Обработанные" },
  { key: "all", label: "Все" },
];

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status = "new" } = await searchParams;
  const rows = await getRequests(status);

  return (
    <>
      <PageHeader
        title="Заявки"
        subtitle="Обращения из бота — сценарии 3–9 и реакция обострения"
      />

      {isDemo() && <DemoNotice />}

      <div className="flex gap-1">
        {TABS.map((t) => (
          <Link
            key={t.key}
            href={`/leads?status=${t.key}`}
            className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
              status === t.key
                ? "bg-[var(--accent-soft)] font-medium text-[var(--accent)]"
                : "text-[var(--text-muted)] hover:bg-[var(--surface-2)]"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </div>

      <Card>
        {rows.length === 0 ? (
          <EmptyState>Нет заявок в этом разделе.</EmptyState>
        ) : (
          <div className="scroll-x">
            <table className="w-full">
              <thead className="border-b border-[var(--border)]">
                <tr>
                  <Th>Когда</Th>
                  <Th>Тип</Th>
                  <Th>ФИО</Th>
                  <Th>Телефон</Th>
                  <Th>Статус</Th>
                  <Th>{""}</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {rows.map((r) => (
                  <LeadRow key={r.id} row={r} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
