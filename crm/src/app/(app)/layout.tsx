import { redirect } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { createClient } from "@/lib/supabase/server";
import { supabaseConfigured } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  let userEmail: string | null = null;

  if (supabaseConfigured()) {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) redirect("/login");
    userEmail = user.email ?? null;
  }

  async function signOut() {
    "use server";
    if (supabaseConfigured()) {
      const supabase = await createClient();
      await supabase.auth.signOut();
    }
    redirect("/login");
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar userEmail={userEmail} signOut={signOut} />
      <main className="min-w-0 flex-1 px-6 py-6">
        <div className="mx-auto max-w-6xl space-y-6">{children}</div>
      </main>
    </div>
  );
}
