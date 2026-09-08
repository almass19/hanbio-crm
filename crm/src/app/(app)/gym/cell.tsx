"use client";

import { useState, useTransition } from "react";
import type { GymBookingRow } from "@/lib/types";
import { clearGymCell, saveGymCell } from "./actions";

export function GymCell({
  date,
  slot,
  seat,
  booking,
}: {
  date: string;
  slot: string;
  seat: number;
  booking?: GymBookingRow;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(booking?.full_name ?? "");
  const [phone, setPhone] = useState(booking?.phone ?? "");
  const [pending, start] = useTransition();

  if (!editing) {
    return (
      <td
        onClick={() => setEditing(true)}
        title={booking ? `${booking.full_name} · ${booking.phone}` : "Записать"}
        className={`cursor-pointer border-b border-r border-[var(--border)] px-2 py-2 align-top leading-tight transition-shadow hover:ring-2 hover:ring-inset hover:ring-[var(--accent)] ${
          booking ? "bg-[var(--accent-soft)]" : "bg-[var(--surface)]"
        }`}
      >
        {booking ? (
          booking.full_name
        ) : (
          <span className="text-[var(--text-muted)]">＋</span>
        )}
      </td>
    );
  }

  const commit = (fn: () => Promise<void>) =>
    start(async () => {
      await fn();
      setEditing(false);
    });

  return (
    <td className="border-b border-r border-[var(--border)] bg-[var(--surface)] p-1 align-top">
      <div className="flex min-w-[130px] flex-col gap-1">
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="ФИО"
          className="w-full rounded border border-[var(--border)] px-1.5 py-1 text-xs outline-none focus:border-[var(--accent)]"
        />
        <input
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="Телефон"
          inputMode="tel"
          className="w-full rounded border border-[var(--border)] px-1.5 py-1 text-xs outline-none focus:border-[var(--accent)]"
        />
        <div className="flex flex-wrap gap-1">
          <button
            disabled={pending || !name.trim()}
            onClick={() =>
              commit(() =>
                saveGymCell(date, slot, seat, {
                  id: booking?.id,
                  full_name: name,
                  phone,
                }),
              )
            }
            className="rounded bg-[var(--accent)] px-2 py-0.5 text-xs font-medium text-[var(--accent-ink)] disabled:opacity-50"
          >
            ОК
          </button>
          {booking && (
            <button
              disabled={pending}
              onClick={() => commit(() => clearGymCell(booking.id))}
              className="rounded border border-[var(--border)] px-2 py-0.5 text-xs"
            >
              Очистить
            </button>
          )}
          <button
            onClick={() => {
              setName(booking?.full_name ?? "");
              setPhone(booking?.phone ?? "");
              setEditing(false);
            }}
            className="rounded border border-[var(--border)] px-2 py-0.5 text-xs"
          >
            ✕
          </button>
        </div>
      </div>
    </td>
  );
}
