-- ============================================
-- Qalb Taskini — Yetishmayotgan ustunlar
-- Supabase SQL Editor'da ishga tushiring
-- ============================================
-- Migration 001'ning oxirgi ikki qatori (arabic, meaning) keyinroq qo'shilgan
-- edi va ba'zi bazalarda ishga tushmay qolgan. Bu migratsiya ularni to'ldiradi.
-- Idempotent — bir necha marta ishga tushirsa ham xavfsiz.

-- Zikrlar jadvaliga arabcha matn ustuni (Tahrirlash → arabcha uchun)
ALTER TABLE dhikrs ADD COLUMN IF NOT EXISTS arabic text DEFAULT '';

-- Duolar jadvaliga ma'no ustuni (standart duolar ma'nosi uchun)
ALTER TABLE duas ADD COLUMN IF NOT EXISTS meaning text DEFAULT '';
