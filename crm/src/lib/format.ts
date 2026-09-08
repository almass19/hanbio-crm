const TZ = "Asia/Almaty";

const dateFmt = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: TZ,
});

const dateTimeFmt = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: TZ,
});

/** ISO date ("2026-09-11") или timestamp -> "11.09.2026". */
export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = value.length <= 10 ? new Date(`${value}T00:00:00`) : new Date(value);
  return Number.isNaN(d.getTime()) ? value : dateFmt.format(d);
}

/** ISO timestamp -> "11.09.2026 14:30". */
export function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : dateTimeFmt.format(d);
}

/** "+77012223344" -> "+7 701 222 33 44". */
export function fmtPhone(value: string | null | undefined): string {
  if (!value) return "—";
  const digits = value.replace(/\D/g, "");
  if (digits.length === 11) {
    const d = digits;
    return `+${d[0]} ${d.slice(1, 4)} ${d.slice(4, 7)} ${d.slice(7, 9)} ${d.slice(9)}`;
  }
  return value;
}

export function initials(name: string | null | undefined): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase() ?? "").join("") || "?";
}

/** Ключ клиента — нормализованный телефон (или "—"). */
export function clientKey(phone: string | null | undefined): string {
  const digits = (phone ?? "").replace(/\D/g, "");
  return digits ? digits.slice(-10) : "—";
}
