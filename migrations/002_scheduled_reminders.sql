-- ============================================
-- Qalb Taskini — Kechiktirilgan (bir martalik) eslatmalar
-- Supabase SQL Editor'da ishga tushiring
-- ============================================
-- Maqsad: "1 soatdan so'ng", "Kechqurun", "Uxlashdan oldin" kabi
-- bir martalik eslatmalar bot restart bo'lganda yo'qolmasin.
-- Ilgari ular xotirada (APScheduler) saqlanardi va GitHub Actions
-- botni har ~5 soatda o'chirib-yoqqanda butunlay yo'qolardi.

CREATE TABLE IF NOT EXISTS scheduled_reminders (
    id serial PRIMARY KEY,
    user_id bigint NOT NULL,
    run_at timestamptz NOT NULL,   -- eslatma yuboriladigan aniq vaqt
    kind text NOT NULL DEFAULT 'shaxsiy',
    sent boolean NOT NULL DEFAULT false,
    created_at timestamptz DEFAULT now()
);

-- Har daqiqa "yuborilishi kerak bo'lgan" eslatmalarni tez topish uchun
CREATE INDEX IF NOT EXISTS idx_sched_rem_pending
    ON scheduled_reminders (run_at)
    WHERE sent = false;

-- Bot ma'lumot yoza olishi uchun RLS o'chiriladi (loyihaning boshqa jadvallariga mos)
ALTER TABLE scheduled_reminders DISABLE ROW LEVEL SECURITY;
