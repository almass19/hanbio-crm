"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";
import { supabaseConfigured } from "@/components/ui";

export async function setRequestStatus(id: number, status: "new" | "processed") {
  if (!supabaseConfigured()) return; // демо-режим — записи в БД нет
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  await supabase
    .from("requests")
    .update({
      status,
      processed_at: status === "processed" ? new Date().toISOString() : null,
      processed_by: status === "processed" ? (user?.id ?? null) : null,
    })
    .eq("id", id);

  revalidatePath("/leads");
  revalidatePath("/");
}

export async function setRequestComment(id: number, comment: string) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  await supabase
    .from("requests")
    .update({ admin_comment: comment.trim() || null })
    .eq("id", id);
  revalidatePath("/leads");
}

export async function setRequestContact(
  id: number,
  data: { full_name: string; phone: string },
) {
  if (!supabaseConfigured()) return;
  const supabase = await createClient();
  await supabase
    .from("requests")
    .update({
      full_name: data.full_name.trim() || null,
      phone: data.phone.trim() || null,
    })
    .eq("id", id);
  revalidatePath("/leads");
  revalidatePath("/clients");
}
