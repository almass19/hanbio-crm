"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const configured =
    !!process.env.NEXT_PUBLIC_SUPABASE_URL &&
    !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setError("Неверная почта или пароль");
        return;
      }
      router.replace("/");
      router.refresh();
    } catch {
      setError("Не удалось подключиться к Supabase");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <div className="text-lg font-semibold tracking-tight">ХанБио CRM</div>
          <div className="text-sm text-[var(--text-muted)]">
            Панель администратора
          </div>
        </div>

        {!configured && (
          <p className="mb-4 rounded-lg bg-[var(--warn-bg)] px-3 py-2 text-xs text-[var(--warn-fg)]">
            Supabase ещё не подключён — вход не сработает, пока не заданы
            переменные окружения.
          </p>
        )}

        <form
          onSubmit={onSubmit}
          className="space-y-3 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
        >
          <label className="block text-sm">
            <span className="text-[var(--text-muted)]">Почта</span>
            <input
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
            />
          </label>
          <label className="block text-sm">
            <span className="text-[var(--text-muted)]">Пароль</span>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
            />
          </label>

          {error && <p className="text-sm text-[var(--warn-fg)]">{error}</p>}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-[var(--accent)] px-3 py-2 text-sm font-medium text-[var(--accent-ink)] transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {busy ? "Вход…" : "Войти"}
          </button>
        </form>

        <p className="mt-4 text-xs text-[var(--text-muted)]">
          Аккаунты создаются в Supabase → Authentication → Users.
        </p>
      </div>
    </main>
  );
}
