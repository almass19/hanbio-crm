import { getInstructorBookings, isDemo } from "@/lib/queries";
import { Card, DemoNotice, EmptyState, PageHeader, Th } from "@/components/ui";
import { InstructorRow } from "./row";
import { AddInstructorRow } from "./new-row";

export const dynamic = "force-dynamic";

export default async function InstructorPage() {
  const rows = await getInstructorBookings();
  const pending = rows.filter((r) => r.status === "Не обработан").length;

  return (
    <>
      <PageHeader
        title="Записи к инструктору"
        subtitle={
          pending > 0 ? `${pending} не обработано` : "Все записи обработаны"
        }
      />

      {isDemo() && <DemoNotice />}

      <AddInstructorRow />

      <Card>
        {rows.length === 0 ? (
          <EmptyState>Пока нет записей к инструктору.</EmptyState>
        ) : (
          <div className="scroll-x">
            <table className="w-full">
              <thead className="border-b border-[var(--border)]">
                <tr>
                  <Th>Дата</Th>
                  <Th>Время</Th>
                  <Th>ФИО</Th>
                  <Th>Инструктор</Th>
                  <Th>Телефон</Th>
                  <Th>Возраст</Th>
                  <Th>Статус</Th>
                  <Th>Программы и комментарии</Th>
                  <Th>{""}</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {rows.map((r) => (
                  <InstructorRow key={r.id} row={r} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
