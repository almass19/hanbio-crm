"use client";

import { useState, useTransition } from "react";
import { createInstructorBooking } from "./actions";

const inputCls =
  "rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-sm outline-none focus:border-[var(--accent)]";

const empty = {
  session_date: "",
  session_time: "",
  full_name: "",
  phone: "",
  instructor: "",
  age: "",
};

export function AddInstructorRow() {
  const [open, setOpen] = useState(false);
  const [f, setF] = useState(empty);
  const [pending, start] = useTransition();
  const set = (k: keyof typeof f, v: string) => setF((p) => ({ ...p, [k]: v }));

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="rounded-lg border border-dashed border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-muted)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
      >
        + Добавить запись
      </button>
    );
  }

  const valid = f.session_date && f.session_time.trim() && f.full_name.trim();

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-3">
      <div className="flex flex-wrap items-end gap-2">
        <label className="text-xs text-[var(--text-muted)]">
          Дата
          <input
            type="date"
            value={f.session_date}
            onChange={(e) => set("session_date", e.target.value)}
            className={`${inputCls} mt-0.5 block w-36`}
          />
        </label>
        <label className="text-xs text-[var(--text-muted)]">
          Время
          <input
            value={f.session_time}
            onChange={(e) => set("session_time", e.target.value)}
            placeholder="15:00"
            className={`${inputCls} mt-0.5 block w-24`}
          />
        </label>
        <label className="text-xs text-[var(--text-muted)]">
          ФИО
          <input
            value={f.full_name}
            onChange={(e) => set("full_name", e.target.value)}
            className={`${inputCls} mt-0.5 block w-56`}
          />
        </label>
        <label className="text-xs text-[var(--text-muted)]">
          Телефон
          <input
            value={f.phone}
            onChange={(e) => set("phone", e.target.value)}
            placeholder="+7…"
            className={`${inputCls} mt-0.5 block w-40`}
          />
        </label>
        <label className="text-xs text-[var(--text-muted)]">
          Инструктор
          <input
            value={f.instructor}
            onChange={(e) => set("instructor", e.target.value)}
            className={`${inputCls} mt-0.5 block w-40`}
          />
        </label>
        <label className="text-xs text-[var(--text-muted)]">
          Возраст
          <input
            value={f.age}
            inputMode="numeric"
            onChange={(e) => set("age", e.target.value.replace(/\D/g, ""))}
            className={`${inputCls} mt-0.5 block w-16`}
          />
        </label>
        <button
          disabled={pending || !valid}
          onClick={() =>
            start(async () => {
              await createInstructorBooking({
                ...f,
                age: f.age.trim() ? Number(f.age) : null,
                instructor: f.instructor.trim() || null,
              });
              setF(empty);
              setOpen(false);
            })
          }
          className="rounded-md bg-[var(--accent)] px-3 py-1.5 text-sm font-medium text-[var(--accent-ink)] disabled:opacity-50"
        >
          Добавить
        </button>
        <button
          onClick={() => {
            setF(empty);
            setOpen(false);
          }}
          className="rounded-md border border-[var(--border)] px-3 py-1.5 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );
}
