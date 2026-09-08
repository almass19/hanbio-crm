import Link from "next/link";
import { getGymBookings, isDemo, todayIso } from "@/lib/queries";
import { fmtDate } from "@/lib/format";
import {
  APPARATUS_NUMBERS,
  GYM_SLOTS,
  weekdayAbbr,
} from "@/lib/schedule";
import { Card, DemoNotice, PageHeader } from "@/components/ui";
import type { GymBookingRow } from "@/lib/types";
import { GymCell } from "./cell";

export const dynamic = "force-dynamic";

/** slot -> seat -> booking, для одного дня */
function grid(rows: GymBookingRow[]) {
  const m = new Map<string, Map<number, GymBookingRow>>();
  for (const r of rows) {
    const slot = m.get(r.session_time) ?? new Map<number, GymBookingRow>();
    slot.set(r.seat_number, r);
    m.set(r.session_time, slot);
  }
  return m;
}

export default async function GymPage({
  searchParams,
}: {
  searchParams: Promise<{ d?: string }>;
}) {
  const rows = await getGymBookings(todayIso());
  const booked = [...new Set(rows.map((r) => r.session_date))].sort();
  const dates = booked.length ? booked : [todayIso()];

  const { d } = await searchParams;
  const active = d && dates.includes(d) ? d : dates[0];
  const dayRows = rows.filter((r) => r.session_date === active);
  const g = grid(dayRows);

  return (
    <>
      <PageHeader
        title="Общий зал"
        subtitle="Сетка «слот × аппарат» — как в таблице расписания"
      />

      {isDemo() && <DemoNotice />}

      <div className="flex flex-wrap gap-1">
        {dates.map((date) => (
          <Link
            key={date}
            href={`/gym?d=${date}`}
            className={`rounded-lg px-3 py-1.5 text-sm tabular-nums transition-colors ${
              date === active
                ? "bg-[var(--accent-soft)] font-medium text-[var(--accent)]"
                : "text-[var(--text-muted)] hover:bg-[var(--surface-2)]"
            }`}
          >
            {fmtDate(date)} <span className="opacity-60">{weekdayAbbr(date)}</span>
          </Link>
        ))}
      </div>

      <Card>
        <div className="scroll-x">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 min-w-[110px] border-b border-r border-[var(--border)] bg-[var(--surface-2)] px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                  Время
                </th>
                {APPARATUS_NUMBERS.map((n) => (
                  <th
                    key={n}
                    className="min-w-[132px] border-b border-r border-[var(--border)] bg-[var(--surface-2)] px-2 py-2 text-left text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]"
                  >
                    Аппарат {n}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {GYM_SLOTS.map((slot) => {
                const slotMap = g.get(slot);
                return (
                  <tr key={slot}>
                    <td className="sticky left-0 z-10 whitespace-nowrap border-b border-r border-[var(--border)] bg-[var(--surface)] px-2 py-2 font-medium tabular-nums text-[var(--text-muted)]">
                      {slot}
                    </td>
                    {APPARATUS_NUMBERS.map((n) => (
                      <GymCell
                        key={n}
                        date={active}
                        slot={slot}
                        seat={n}
                        booking={slotMap?.get(n)}
                      />
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <p className="text-xs text-[var(--text-muted)]">
        Кликни по ячейке, чтобы записать клиента или изменить/освободить.
        Зелёная — занятый аппарат. Бот пишет сюда же.
      </p>
    </>
  );
}
