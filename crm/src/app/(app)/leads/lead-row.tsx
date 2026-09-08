"use client";

import { useState, useTransition } from "react";
import { Badge, Td } from "@/components/ui";
import { fmtDateTime, fmtPhone } from "@/lib/format";
import { scenarioLabel, type RequestRow } from "@/lib/types";
import {
  setRequestComment,
  setRequestContact,
  setRequestStatus,
} from "./actions";

function payloadLines(payload: Record<string, unknown>): [string, string][] {
  return Object.entries(payload)
    .filter(([, v]) => v !== "" && v != null)
    .map(([k, v]) => [k, String(v)]);
}

export function LeadRow({ row }: { row: RequestRow }) {
  const [open, setOpen] = useState(false);
  const [comment, setComment] = useState(row.admin_comment ?? "");
  const [name, setName] = useState(row.full_name ?? "");
  const [phone, setPhone] = useState(row.phone ?? "");
  const [pending, start] = useTransition();
  const processed = row.status === "processed";
  const contactDirty =
    name !== (row.full_name ?? "") || phone !== (row.phone ?? "");

  return (
    <>
      <tr className="hover:bg-[var(--surface-2)]">
        <Td className="whitespace-nowrap text-[var(--text-muted)]">
          {fmtDateTime(row.created_at)}
        </Td>
        <Td>{scenarioLabel(row.scenario_key)}</Td>
        <Td>{row.full_name ?? "—"}</Td>
        <Td className="whitespace-nowrap tabular-nums">{fmtPhone(row.phone)}</Td>
        <Td>
          <Badge tone={processed ? "ok" : "warn"}>
            {processed ? "Обработана" : "Новая"}
          </Badge>
        </Td>
        <Td className="whitespace-nowrap text-right">
          <button
            onClick={() => setOpen((v) => !v)}
            className="mr-2 text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
          >
            {open ? "Скрыть" : "Детали"}
          </button>
          <button
            disabled={pending}
            onClick={() =>
              start(() =>
                setRequestStatus(row.id, processed ? "new" : "processed"),
              )
            }
            className="rounded-md border border-[var(--border)] px-2 py-1 text-sm hover:bg-[var(--surface)] disabled:opacity-50"
          >
            {processed ? "Вернуть в новые" : "Обработано"}
          </button>
        </Td>
      </tr>

      {open && (
        <tr className="bg-[var(--surface-2)]">
          <td colSpan={6} className="px-3 py-3">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-3">
                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                    Контакт
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="ФИО"
                      className="w-48 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-sm outline-none focus:border-[var(--accent)]"
                    />
                    <input
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="Телефон"
                      className="w-40 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 py-1 text-sm tabular-nums outline-none focus:border-[var(--accent)]"
                    />
                    {contactDirty && (
                      <button
                        disabled={pending}
                        onClick={() =>
                          start(() =>
                            setRequestContact(row.id, {
                              full_name: name,
                              phone,
                            }),
                          )
                        }
                        className="rounded-md bg-[var(--accent)] px-2 py-1 text-xs font-medium text-[var(--accent-ink)] disabled:opacity-50"
                      >
                        Сохранить
                      </button>
                    )}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                    Данные заявки
                  </div>
                  <dl className="space-y-0.5 text-sm">
                    {payloadLines(row.payload).length === 0 && (
                      <span className="text-[var(--text-muted)]">—</span>
                    )}
                    {payloadLines(row.payload).map(([k, v]) => (
                      <div key={k} className="flex gap-2">
                        <dt className="min-w-28 text-[var(--text-muted)]">
                          {k}
                        </dt>
                        <dd>{v}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
              <div>
                <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                  Комментарий администратора
                </div>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
                />
                <button
                  disabled={pending || comment === (row.admin_comment ?? "")}
                  onClick={() =>
                    start(() => setRequestComment(row.id, comment))
                  }
                  className="mt-2 rounded-md bg-[var(--accent)] px-3 py-1.5 text-sm font-medium text-[var(--accent-ink)] hover:opacity-90 disabled:opacity-50"
                >
                  Сохранить комментарий
                </button>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
