import { createClient } from "@/lib/supabase/server";
import { supabaseConfigured } from "@/components/ui";
import {
  DEMO_GYM,
  DEMO_INSTRUCTOR,
  DEMO_REQUESTS,
} from "@/lib/demo";
import type {
  GymBookingRow,
  InstructorBookingRow,
  RequestRow,
} from "@/lib/types";

function todayIso(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Almaty" }).format(
    new Date(),
  );
}

export const isDemo = () => !supabaseConfigured();

// ---------------------------------------------------------------------------
//  Dashboard
// ---------------------------------------------------------------------------

export interface DashboardData {
  demo: boolean;
  newRequests: number;
  requestsToday: number;
  instructorPending: number;
  gymUpcoming: number;
  recent: RequestRow[];
}

export async function getDashboard(): Promise<DashboardData> {
  if (isDemo()) {
    const today = todayIso();
    return {
      demo: true,
      newRequests: DEMO_REQUESTS.filter((r) => r.status === "new").length,
      requestsToday: DEMO_REQUESTS.filter((r) => r.created_at.slice(0, 10) === today)
        .length,
      instructorPending: DEMO_INSTRUCTOR.filter((r) => r.status === "Не обработан")
        .length,
      gymUpcoming: DEMO_GYM.filter((b) => b.session_date >= today).length,
      recent: [...DEMO_REQUESTS]
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .slice(0, 8),
    };
  }

  const supabase = await createClient();
  const today = todayIso();
  const dayStart = `${today}T00:00:00`;

  const [newReq, todayReq, instrPending, gymUp, recent] = await Promise.all([
    supabase
      .from("requests")
      .select("id", { count: "exact", head: true })
      .eq("status", "new"),
    supabase
      .from("requests")
      .select("id", { count: "exact", head: true })
      .gte("created_at", dayStart),
    supabase
      .from("instructor_bookings")
      .select("id", { count: "exact", head: true })
      .eq("status", "Не обработан"),
    supabase
      .from("gym_bookings")
      .select("id", { count: "exact", head: true })
      .gte("session_date", today)
      .eq("status", "active"),
    supabase
      .from("requests")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(8),
  ]);

  return {
    demo: false,
    newRequests: newReq.count ?? 0,
    requestsToday: todayReq.count ?? 0,
    instructorPending: instrPending.count ?? 0,
    gymUpcoming: gymUp.count ?? 0,
    recent: (recent.data as RequestRow[] | null) ?? [],
  };
}

// ---------------------------------------------------------------------------
//  Lists
// ---------------------------------------------------------------------------

export async function getRequests(status: string): Promise<RequestRow[]> {
  if (isDemo()) {
    const rows = [...DEMO_REQUESTS].sort((a, b) =>
      b.created_at.localeCompare(a.created_at),
    );
    if (status === "new" || status === "processed")
      return rows.filter((r) => r.status === status);
    return rows;
  }
  const supabase = await createClient();
  let q = supabase
    .from("requests")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(500);
  if (status === "new" || status === "processed") q = q.eq("status", status);
  const { data } = await q;
  return (data as RequestRow[] | null) ?? [];
}

export async function getInstructorBookings(): Promise<InstructorBookingRow[]> {
  if (isDemo()) {
    return [...DEMO_INSTRUCTOR].sort(
      (a, b) =>
        b.session_date.localeCompare(a.session_date) ||
        a.session_time.localeCompare(b.session_time),
    );
  }
  const supabase = await createClient();
  const { data } = await supabase
    .from("instructor_bookings")
    .select("*")
    .order("session_date", { ascending: false })
    .order("session_time", { ascending: true })
    .limit(500);
  return (data as InstructorBookingRow[] | null) ?? [];
}

export async function getGymBookings(fromDate: string): Promise<GymBookingRow[]> {
  if (isDemo()) {
    return DEMO_GYM.filter((b) => b.session_date >= fromDate).sort(
      (a, b) =>
        a.session_date.localeCompare(b.session_date) ||
        a.session_time.localeCompare(b.session_time) ||
        a.seat_number - b.seat_number,
    );
  }
  const supabase = await createClient();
  const { data } = await supabase
    .from("gym_bookings")
    .select("*")
    .gte("session_date", fromDate)
    .eq("status", "active")
    .order("session_date", { ascending: true })
    .order("session_time", { ascending: true })
    .order("seat_number", { ascending: true })
    .limit(1000);
  return (data as GymBookingRow[] | null) ?? [];
}

// ---------------------------------------------------------------------------
//  Clients (aggregate by phone across all sources)
// ---------------------------------------------------------------------------

export interface ClientSummary {
  key: string;
  name: string;
  phone: string | null;
  requests: number;
  gym: number;
  instructor: number;
  last: string;
}

type NamePhone = {
  full_name: string | null;
  phone: string | null;
  created_at: string;
};

const phoneKey = (p: string | null) =>
  (p ?? "").replace(/\D/g, "").slice(-10);

function aggregate(
  req: NamePhone[],
  gym: NamePhone[],
  instr: NamePhone[],
): ClientSummary[] {
  const map = new Map<string, ClientSummary>();

  const ingest = (rows: NamePhone[], field: "requests" | "gym" | "instructor") => {
    for (const r of rows) {
      const key = phoneKey(r.phone) || (r.full_name ?? "—");
      const existing =
        map.get(key) ??
        ({
          key,
          name: r.full_name ?? "—",
          phone: r.phone ?? null,
          requests: 0,
          gym: 0,
          instructor: 0,
          last: r.created_at,
        } satisfies ClientSummary);
      existing[field] += 1;
      if (r.full_name && existing.name === "—") existing.name = r.full_name;
      if (r.created_at > existing.last) existing.last = r.created_at;
      map.set(key, existing);
    }
  };

  ingest(req, "requests");
  ingest(gym, "gym");
  ingest(instr, "instructor");

  return [...map.values()].sort((a, b) => b.last.localeCompare(a.last));
}

export async function getClients(): Promise<ClientSummary[]> {
  if (isDemo()) {
    return aggregate(DEMO_REQUESTS, DEMO_GYM, DEMO_INSTRUCTOR);
  }
  const supabase = await createClient();
  const [req, gym, instr] = await Promise.all([
    supabase.from("requests").select("full_name, phone, created_at").limit(2000),
    supabase
      .from("gym_bookings")
      .select("full_name, phone, created_at")
      .limit(2000),
    supabase
      .from("instructor_bookings")
      .select("full_name, phone, created_at")
      .limit(2000),
  ]);
  return aggregate(
    (req.data as NamePhone[] | null) ?? [],
    (gym.data as NamePhone[] | null) ?? [],
    (instr.data as NamePhone[] | null) ?? [],
  );
}

export interface ClientDetail {
  key: string;
  name: string;
  phone: string | null;
  requests: RequestRow[];
  gym: GymBookingRow[];
  instructor: InstructorBookingRow[];
}

export async function getClientDetail(key: string): Promise<ClientDetail | null> {
  let requests: RequestRow[];
  let gymRows: GymBookingRow[];
  let instructorRows: InstructorBookingRow[];

  if (isDemo()) {
    const match = (p: string | null) => phoneKey(p) === key || p === key;
    requests = DEMO_REQUESTS.filter((r) => match(r.phone));
    gymRows = DEMO_GYM.filter((b) => match(b.phone));
    instructorRows = DEMO_INSTRUCTOR.filter((b) => match(b.phone));
  } else {
    const supabase = await createClient();
    const like = `%${key}%`;
    const [req, gym, instr] = await Promise.all([
      supabase
        .from("requests")
        .select("*")
        .ilike("phone", like)
        .order("created_at", { ascending: false }),
      supabase
        .from("gym_bookings")
        .select("*")
        .ilike("phone", like)
        .order("session_date", { ascending: false }),
      supabase
        .from("instructor_bookings")
        .select("*")
        .ilike("phone", like)
        .order("session_date", { ascending: false }),
    ]);
    requests = (req.data as RequestRow[] | null) ?? [];
    gymRows = (gym.data as GymBookingRow[] | null) ?? [];
    instructorRows = (instr.data as InstructorBookingRow[] | null) ?? [];
  }

  if (!requests.length && !gymRows.length && !instructorRows.length) return null;

  const name =
    requests[0]?.full_name ??
    gymRows[0]?.full_name ??
    instructorRows[0]?.full_name ??
    "—";
  const phone =
    requests[0]?.phone ?? gymRows[0]?.phone ?? instructorRows[0]?.phone ?? null;

  return { key, name, phone, requests, gym: gymRows, instructor: instructorRows };
}

export { todayIso };
