import Link from "next/link";
import { getDashboard } from "@/lib/queries";
import { scenarioLabel } from "@/lib/types";
import { fmtDateTime, fmtPhone } from "@/lib/format";
import {
  Card,
  DemoNotice,
  EmptyState,
  PageHeader,
  StatCard,
  Td,
  Th,
} from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const d = await getDashboard();

  return (
    <>
      <PageHeader
        title="Дашборд"
        subtitle="Сводка по заявкам и записям"
      />

      {d.demo && <DemoNotice />}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Новых заявок" value={d.newRequests} />
        <StatCard label="Заявок сегодня" value={d.requestsToday} />
        <StatCard
          label="Инструктор: не обработано"
          value={d.instructorPending}
        />
        <StatCard label="Записей в зал впереди" value={d.gymUpcoming} />
      </div>

      <Card>
        <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
          <h2 className="text-sm font-semibold">Последние заявки</h2>
          <Link
            href="/leads"
            className="text-sm text-[var(--accent)] hover:underline"
          >
            Все заявки →
          </Link>
        </div>
        {d.recent.length === 0 ? (
          <EmptyState>Пока нет заявок.</EmptyState>
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
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {d.recent.map((r) => (
                  <tr key={r.id}>
                    <Td className="whitespace-nowrap text-[var(--text-muted)]">
                      {fmtDateTime(r.created_at)}
                    </Td>
                    <Td>{scenarioLabel(r.scenario_key)}</Td>
                    <Td>{r.full_name ?? "—"}</Td>
                    <Td className="whitespace-nowrap tabular-nums">
                      {fmtPhone(r.phone)}
                    </Td>
                    <Td>
                      {r.status === "new" ? "Новая" : "Обработана"}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
