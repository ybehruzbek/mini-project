-- ============================================
-- Qalb Taskini — Namoz & Duo'lar Migratsiyasi
-- Supabase SQL Editor'da ishga tushiring
-- ============================================

-- 1. Users jadvaliga yangi ustunlar
ALTER TABLE users ADD COLUMN IF NOT EXISTS city text DEFAULT 'Toshkent';
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone text DEFAULT 'Asia/Tashkent';
ALTER TABLE users ADD COLUMN IF NOT EXISTS prayer_notifications boolean DEFAULT true;

-- 2. Duo'lar jadvali
CREATE TABLE IF NOT EXISTS duas (
    id serial PRIMARY KEY,
    user_id bigint NOT NULL,
    text text NOT NULL,
    arabic text,
    category text NOT NULL DEFAULT 'custom',
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

-- 3. user_reminders jadvaliga yangi ustunlar
ALTER TABLE user_reminders ADD COLUMN IF NOT EXISTS type text DEFAULT 'dhikr';
ALTER TABLE user_reminders ADD COLUMN IF NOT EXISTS label text;

-- 4. Namoz vaqtlari cache jadvali
CREATE TABLE IF NOT EXISTS prayer_cache (
    id serial PRIMARY KEY,
    city text NOT NULL,
    date text NOT NULL,
    fajr text,
    dhuhr text,
    asr text,
    maghrib text,
    isha text,
    fajr_notify text,
    dhuhr_notify text,
    asr_notify text,
    maghrib_notify text,
    isha_notify text,
    created_at timestamp with time zone DEFAULT now(),
    UNIQUE(city, date)
);

-- 5. Indekslar
CREATE INDEX IF NOT EXISTS idx_duas_user_id ON duas(user_id);
CREATE INDEX IF NOT EXISTS idx_duas_category ON duas(category);
CREATE INDEX IF NOT EXISTS idx_prayer_cache_city_date ON prayer_cache(city, date);
CREATE INDEX IF NOT EXISTS idx_user_reminders_type ON user_reminders(type);

-- 6. RLS policies (ixtiyoriy — agar RLS yoqilgan bo'lsa)
-- ALTER TABLE duas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE prayer_cache ENABLE ROW LEVEL SECURITY;
