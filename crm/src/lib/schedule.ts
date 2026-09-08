/** Сеансовая сетка зала — та же, что в таблице расписания и в боте
 *  (bot/services/gym_sheet.py). Держим копию здесь для вида «как в таблице». */

export const GYM_SLOTS: string[] = [
  "10:10 - 10:40",
  "11:00 - 11:30",
  "11:50 - 12:20",
  "12:40 - 13:10",
  "13:30 - 14:00",
  "14:20 - 14:50",
  "15:10 - 15:40",
  "16:00 - 16:30",
  "16:50 - 17:20",
  "17:40 - 18:10",
  "18:30 - 19:00",
  "19:20 - 19:50",
];

export const GYM_APPARATUS_COUNT = 8;

export const APPARATUS_NUMBERS: number[] = Array.from(
  { length: GYM_APPARATUS_COUNT },
  (_, i) => i + 1,
);

const WEEKDAY_ABBR = ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"];

/** "2026-09-24" -> "Чт". */
export function weekdayAbbr(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime()) ? "" : WEEKDAY_ABBR[d.getDay()];
}
