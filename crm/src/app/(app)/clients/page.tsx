import Link from "next/link";
import { getClients, isDemo } from "@/lib/queries";
import { fmtDateTime, fmtPhone } from "@/lib/format";
import { Card, DemoNotice, EmptyState, PageHeader, Td, Th } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function ClientsPage() {
  const clients = await getClients();

  return (
    <>
      <PageHeader
        title="Клиенты"
        subtitle="Сгруппированы по номеру телефона — из всех записей и заявок"
      />

      {isDemo() && <DemoNotice />}

      <Card>
        {clients.length === 0 ? (
          <EmptyState>Пока нет данных о клиентах.</EmptyState>
        ) : (
          <div className="scroll-x">
            <table className="w-full">
              <thead className="border-b border-[var(--border)]">
                <tr>
                  <Th>ФИО</Th>
                  <Th>Телефон</Th>
                  <Th>Заявок</Th>
                  <Th>Зал</Th>
                  <Th>Инструктор</Th>
                  <Th>Последняя активность</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {clients.map((c) => (
                  <tr key={c.key} className="hover:bg-[var(--surface-2)]">
                    <Td>
                      <Link
                        href={`/clients/${encodeURIComponent(c.key)}`}
                        className="font-medium text-[var(--accent)] hover:underline"
                      >
                        {c.name}
                      </Link>
                    </Td>
                    <Td className="whitespace-nowrap tabular-nums">
                      {fmtPhone(c.phone)}
                    </Td>
                    <Td className="tabular-nums">{c.requests}</Td>
                    <Td className="tabular-nums">{c.gym}</Td>
                    <Td className="tabular-nums">{c.instructor}</Td>
                    <Td className="whitespace-nowrap text-[var(--text-muted)]">
                      {fmtDateTime(c.last)}
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
