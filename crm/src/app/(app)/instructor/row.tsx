"use client";

import { useState, useTransition } from "react";
import { Td } from "@/components/ui";
import type { InstructorBookingRow, InstructorStatus } from "@/lib/types";
import {
  deleteInstructorBooking,
  updateInstructorBooking,
} from "./actions";

const STATUSES: InstructorStatus[] = ["Не обработан", "Обработан"];

const inputCls =
  "rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-sm outline-none focus:border-[var(--accent)]";

export function InstructorRow({ row }: { row: InstructorBookingRow }) {
  const [f, setF] = useState({
    session_date: row.session_date,
    session_time: row.session_time,
    full_name: row.full_name,
    phone: row.phone,
    instructor: row.instructor ?? "",
    age: row.age?.toString() ?? "",
    programs_comment: row.programs_comment ?? "",
  });
  const [pending, start] = useTransition();

  const set = (k: keyof typeof f, v: string) => setF((p) => ({ ...p, [k]: v }));

  const dirty =
    f.session_date !== row.session_date ||
    f.session_time !== row.session_time ||
    f.full_name !== row.full_name ||
    f.phone !== row.phone ||
    f.instructor !== (row.instructor ?? "") ||
    f.age !== (row.age?.toString() ?? "") ||
    f.programs_comment !== (row.programs_comment ?? "");

  const save = () =>
    start(() =>
      updateInstructorBooking(row.id, {
        session_date: f.session_date,
        session_time: f.session_time.trim(),
        full_name: f.full_name.trim(),
        phone: f.phone.trim(),
        instructor: f.instructor.trim() || null,
        age: f.age.trim() ? Number(f.age) : null,
        programs_comment: f.programs_comment.trim() || null,
      }),
    );

  const setStatus = (status: InstructorStatus) =>
    start(() => updateInstructorBooking(row.id, { status }));

  return (
    <tr className="hover:bg-[var(--surface-2)]">
      <Td>
        <input
          type="date"
          value={f.session_date}
          onChange={(e) => set("session_date", e.target.value)}
          className={`${inputCls} w-36 tabular-nums`}
        />
      </Td>
      <Td>
        <input
          value={f.session_time}
          onChange={(e) => set("session_time", e.target.value)}
          className={`${inputCls} w-24`}
        />
      </Td>
      <Td>
        <input
          value={f.full_name}
          onChange={(e) => set("full_name", e.target.value)}
          className={`${inputCls} w-48`}
        />
      </Td>
      <Td>
        <input
          value={f.instructor}
          onChange={(e) => set("instructor", e.target.value)}
          placeholder="—"
          className={`${inputCls} w-40`}
        />
      </Td>
      <Td>
        <input
          value={f.phone}
          onChange={(e) => set("phone", e.target.value)}
          className={`${inputCls} w-36 tabular-nums`}
        />
      </Td>
      <Td>
        <input
          value={f.age}
          inputMode="numeric"
          onChange={(e) => set("age", e.target.value.replace(/\D/g, ""))}
          placeholder="—"
          className={`${inputCls} w-14`}
        />
      </Td>
      <Td>
        <select
          value={row.status}
          disabled={pending}
          onChange={(e) => setStatus(e.target.value as InstructorStatus)}
          className={`${inputCls} ${
            row.status === "Обработан"
              ? "text-[var(--ok-fg)]"
              : "text-[var(--warn-fg)]"
          }`}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </Td>
      <Td>
        <textarea
          value={f.programs_comment}
          onChange={(e) => set("programs_comment", e.target.value)}
          rows={1}
          className={`${inputCls} min-h-[34px] w-56`}
        />
      </Td>
      <Td className="whitespace-nowrap text-right">
        {dirty ? (
          <button
            disabled={pending}
            onClick={save}
            className="rounded-md bg-[var(--accent)] px-2 py-1 text-xs font-medium text-[var(--accent-ink)] hover:opacity-90 disabled:opacity-50"
          >
            Сохранить
          </button>
        ) : (
          <button
            disabled={pending}
            onClick={() => {
              if (confirm("Удалить запись?"))
                start(() => deleteInstructorBooking(row.id));
            }}
            className="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--text-muted)] hover:text-[var(--warn-fg)]"
          >
            Удалить
          </button>
        )}
      </Td>
    </tr>
  );
}
