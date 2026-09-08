-- ============================================================================
--  ХанБио CRM + бот — единая схема Postgres (Supabase).
--
--  Вставить целиком в Supabase → SQL Editor → Run на новом проекте.
--  Таблицы users / requests / gym_bookings / instructor_bookings /
--  sheet_sync_queue пишет Telegram-бот (через прямое подключение к Postgres,
--  RLS его не касается). CRM (Next.js) читает/пишет их же через supabase-js
--  под политиками RLS ниже.
-- ============================================================================

-- ---------------------------------------------------------------------------
--  Ядро бота
-- ---------------------------------------------------------------------------

create table if not exists public.users (
    id           bigint generated always as identity primary key,
    telegram_id  bigint unique not null,
    username     text,
    first_name   text,
    phone        text,
    created_at   timestamptz not null default now()
);

create table if not exists public.requests (
    id            bigint generated always as identity primary key,
    user_id       bigint not null references public.users (id),
    scenario_key  text not null,
    payload       jsonb not null default '{}'::jsonb,
    full_name     text,
    phone         text,
    status        text not null default 'new',      -- new | processed
    admin_comment text,
    processed_at  timestamptz,
    processed_by  uuid references auth.users (id),
    created_at    timestamptz not null default now()
);
create index if not exists ix_requests_scenario_key on public.requests (scenario_key);
create index if not exists ix_requests_status       on public.requests (status);
create index if not exists ix_requests_created_at   on public.requests (created_at desc);

create table if not exists public.gym_bookings (
    id            bigint generated always as identity primary key,
    user_id       bigint references public.users (id),  -- null = создано в CRM, не ботом
    session_date  date not null,
    session_time  text not null,                    -- "10:10 - 10:40"
    seat_number   int  not null,                    -- номер аппарата
    full_name     text not null,
    phone         text not null,
    status        text not null default 'active',   -- active | cancelled
    created_at    timestamptz not null default now(),
    constraint uq_gym_slot_seat unique (session_date, session_time, seat_number)
);
create index if not exists ix_gym_bookings_session_date on public.gym_bookings (session_date);

create table if not exists public.instructor_bookings (
    id               bigint generated always as identity primary key,
    user_id          bigint references public.users (id),  -- null = создано в CRM
    session_date     date not null,
    session_time     text not null,
    full_name        text not null,
    phone            text not null,
    -- поля, которые заполняет администратор в CRM (как в листе
    -- «Запись к Инструктору Новая»):
    instructor       text,
    age              int,
    status           text not null default 'Не обработан',  -- Не обработан | Обработан
    programs_comment text,
    created_at       timestamptz not null default now()
);
create index if not exists ix_instructor_bookings_session_date on public.instructor_bookings (session_date);
create index if not exists ix_instructor_bookings_status       on public.instructor_bookings (status);

create table if not exists public.sheet_sync_queue (
    id          bigint generated always as identity primary key,
    sheet_name  text not null,
    row_data    jsonb not null,
    attempts    int not null default 0,
    last_error  text,
    synced_at   timestamptz,
    created_at  timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
--  CRM
-- ---------------------------------------------------------------------------

create table if not exists public.crm_profiles (
    id         uuid primary key references auth.users (id) on delete cascade,
    name       text not null default '',
    role       text not null default 'admin',        -- admin | reception
    created_at timestamptz not null default now()
);

-- профиль заводится автоматически при регистрации пользователя в Supabase Auth
create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.crm_profiles (id, name)
    values (new.id, coalesce(new.raw_user_meta_data ->> 'name', new.email))
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_auth_user();

-- ---------------------------------------------------------------------------
--  RLS — внутренний инструмент: любой залогиненный сотрудник видит и правит всё.
--  Бот ходит в обход RLS (прямое подключение к Postgres).
-- ---------------------------------------------------------------------------

do $$
declare t text;
begin
    foreach t in array array[
        'users', 'requests', 'gym_bookings', 'instructor_bookings',
        'sheet_sync_queue', 'crm_profiles'
    ]
    loop
        execute format('alter table public.%I enable row level security;', t);
        execute format('drop policy if exists "staff_all" on public.%I;', t);
        execute format(
            'create policy "staff_all" on public.%I for all to authenticated using (true) with check (true);',
            t
        );
    end loop;
end $$;

-- ---------------------------------------------------------------------------
--  Realtime — чтобы CRM могла подписываться на новые заявки и записи
-- ---------------------------------------------------------------------------

do $$
begin
    alter publication supabase_realtime add table
        public.requests, public.gym_bookings, public.instructor_bookings;
exception when others then
    -- публикации нет или таблицы уже добавлены — не критично
    null;
end $$;
