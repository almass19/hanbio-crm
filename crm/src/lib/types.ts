/** Строки таблиц Postgres (см. supabase/migrations/0001_init.sql). */

export type RequestStatus = "new" | "processed";

export interface RequestRow {
  id: number;
  user_id: number;
  scenario_key: string;
  payload: Record<string, unknown>;
  full_name: string | null;
  phone: string | null;
  status: RequestStatus;
  admin_comment: string | null;
  processed_at: string | null;
  processed_by: string | null;
  created_at: string;
}

export interface GymBookingRow {
  id: number;
  user_id: number;
  session_date: string;
  session_time: string;
  seat_number: number;
  full_name: string;
  phone: string;
  status: "active" | "cancelled";
  created_at: string;
}

export type InstructorStatus = "Не обработан" | "Обработан";

export interface InstructorBookingRow {
  id: number;
  user_id: number;
  session_date: string;
  session_time: string;
  full_name: string;
  phone: string;
  instructor: string | null;
  age: number | null;
  status: InstructorStatus;
  programs_comment: string | null;
  created_at: string;
}

export interface UserRow {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  phone: string | null;
  created_at: string;
}

/** Человекочитаемые названия сценариев бота. */
export const SCENARIO_LABELS: Record<string, string> = {
  home_program: "Запись на домашнюю программу",
  home_program_plan: "Расписать домашнюю программу",
  emergency: "Реакция обострения",
  consumables: "Покупка расходных материалов",
  inspection: "Техосмотр оборудования",
  contract: "Вопросы по договору",
  other: "Другое обращение",
};

export function scenarioLabel(key: string): string {
  return SCENARIO_LABELS[key] ?? key;
}
