"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { supabaseConfigured } from "@/components/ui";

export async function saveGymCell(
  date: string,
  slot: string,
  seat: number,
  data: { id?: number; full_name: string; phone: string },
) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  const patch = {
    full_name: data.full_name.trim(),
    phone: data.phone.trim() || "—",
  };

  if (data.id) {
    await supabase.from("gym_bookings").update(patch).eq("id", data.id);
  } else {
    await supabase.from("gym_bookings").insert({
      session_date: date,
      session_time: slot,
      seat_number: seat,
      status: "active",
      ...patch,
    });
  }
  revalidatePath("/gym");
  revalidatePath("/");
}

export async function clearGymCell(id: number) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  await supabase.from("gym_bookings").delete().eq("id", id);
  revalidatePath("/gym");
  revalidatePath("/");
}
