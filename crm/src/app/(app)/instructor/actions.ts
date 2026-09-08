"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { supabaseConfigured } from "@/components/ui";
import type { InstructorStatus } from "@/lib/types";

export interface InstructorPatch {
  session_date?: string;
  session_time?: string;
  full_name?: string;
  phone?: string;
  instructor?: string | null;
  age?: number | null;
  status?: InstructorStatus;
  programs_comment?: string | null;
}

function revalidate() {
  revalidatePath("/instructor");
  revalidatePath("/");
  revalidatePath("/clients");
}

export async function updateInstructorBooking(id: number, patch: InstructorPatch) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  await supabase.from("instructor_bookings").update(patch).eq("id", id);
  revalidate();
}

export async function createInstructorBooking(data: {
  session_date: string;
  session_time: string;
  full_name: string;
  phone: string;
  instructor?: string | null;
  age?: number | null;
}) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  await supabase.from("instructor_bookings").insert({
    session_date: data.session_date,
    session_time: data.session_time.trim(),
    full_name: data.full_name.trim(),
    phone: data.phone.trim() || "—",
    instructor: data.instructor?.trim() || null,
    age: data.age ?? null,
    status: "Не обработан",
  });
  revalidate();
}

export async function deleteInstructorBooking(id: number) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  await supabase.from("instructor_bookings").delete().eq("id", id);
  revalidate();
}
