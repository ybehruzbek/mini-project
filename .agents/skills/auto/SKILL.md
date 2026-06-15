---
name: auto
description: "Har bir so'rovda avtomatik skill'larni aniqlash va ishlatish. So'rov yozganda /auto tanlab yuboring — agent o'zi kerakli skill'larni topadi, o'qiydi va xabar beradi."
---

# 🤖 Auto Skill Detector — Yoshlar Dashboard

Foydalanuvchi so'rov yozganda kerakli skill'larni **avtomatik aniqla**, o'qi va ishga tushir.

> **Muhim:** Bu skill har bir `/auto` so'rovda ishga tushadi. Agent bu ko'rsatmalarni qat'iy bajarishi **SHART**.

---

## 📁 Skill joylashuvlari

Skill'lar **3 ta** papkada joylashgan:

| Papka | Joylashuv | Tavsif |
|-------|-----------|--------|
| **Loyiha (.agents)** | `.agents/skills/` | Loyihaga tegishli skill'lar |
| **Loyiha (.agent)** | `.agent/skills/` | Qo'shimcha loyiha skill'lari |
| **Global (~)** | `~/.agents/skills/` | Barcha loyihalar uchun umumiy skill'lar |

---

## 🔄 Jarayon (5 qadam)

### 1-qadam: Kontekstni tushun

1. `.agents/instructions.md` faylini o'qi — loyiha haqida umumiy ma'lumot.
2. Foydalanuvchi so'rovini **to'liq o'qi va tahlil qil**.
3. Ochiq fayllar va cursor pozitsiyasini hisobga ol.

### 2-qadam: Skill'larni aniqla

So'rovni quyidagi **kategoriyalar** bo'yicha tekshir. Bir nechta kategoriya mos kelishi mumkin — **barchasini** tanla.

---

#### 🔴 KRITIK — Har doim avtomatik qo'shiladigan skill'lar

Bu skill'lar ma'lum harakatlardan **OLDIN** har doim o'qilishi kerak:

| Trigger | Skill | Yo'l |
|---------|-------|------|
| Kodni tugataman / yakunlayman deyilganda | `verification-before-completion` | `.agent/skills/verification-before-completion/SKILL.md` |
| `git commit` qilishdan oldin | `conventional-commits` | `.agents/skills/conventional-commits/SKILL.md` |

---

#### 🛠️ DEBUGGING & XATOLIK

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| bug, xato, tuzat, ishlamayapti, error, crash, noto'g'ri, buzilgan, qizil xato | `systematic-debugging` | `.agent/skills/systematic-debugging/SKILL.md` |
| error handling, try-catch, xatolik boshqarish, graceful degradation | `error-handling-patterns` | `.agent/skills/error-handling-patterns/SKILL.md` |
| barcha sahifani tekshir, hamma page, umumiy test | `systematic-debugging` + `verification-before-completion` | `.agent/skills/systematic-debugging/SKILL.md` |

---

#### 🏗️ ARXITEKTURA & REJALASHTIRISH

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| yangi feature, funksiya, qo'sh, yaratish, g'oya, loyiha | `brainstorming` → keyin `writing-plans` | `.agents/skills/brainstorming/SKILL.md` |
| reja, plan, katta vazifa, bosqichma-bosqich, roadmap | `writing-plans` → keyin `executing-plans` | `.agents/skills/writing-plans/SKILL.md` |
| parallel ish, subagent, mustaqil vazifalar, tez bajarish | `subagent-driven-development` | `.agents/skills/subagent-driven-development/SKILL.md` |
| review, tekshir, PR, code review, merge oldin | `requesting-code-review` | `.agent/skills/requesting-code-review/SKILL.md` |
| test, testing, sinov, TDD, unit test, e2e | `test-driven-development` | `.agent/skills/test-driven-development/SKILL.md` |

---

#### ⚛️ FRONTEND & UI

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| next.js, sahifa, route, API route, middleware, layout, SSR, RSC | `next-best-practices` | `.agents/skills/next-best-practices/SKILL.md` |
| react, komponent, component, hook, state, props, context | `vercel-react-best-practices` | `.agents/skills/vercel-react-best-practices/SKILL.md` |
| UI, dizayn, interfeys, frontend, stil, responsive, mobile, chiroyli | `frontend-design` | `.agents/skills/frontend-design/SKILL.md` |
| UI tekshirish, audit, accessibility, UX, a11y, contrast | `web-design-guidelines` | `.agents/skills/web-design-guidelines/SKILL.md` |
| brand, brend, logo, rang, dizayn tizimi, tipografiya, palette | `brand-identity` | `.agent/skills/brand-identity/SKILL.md` |

---

#### 🗄️ BACKEND & DATABASE

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| prisma, database, model, migration, schema, DB, jadval, ustun | `prisma-database-setup` + `prisma-cli` | `~/.agents/skills/prisma-database-setup/SKILL.md` |
| auth, login, session, NextAuth, ro'yxatdan o'tish, himoya, parol | `nextauth-authentication` | `~/.agents/skills/nextauth-authentication/SKILL.md` |

---

#### 🔒 XAVFSIZLIK

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| xavfsizlik, security, himoya, zaiflik, vulnerability | `security-best-practices` + `owasp-top-10` | `~/.agents/skills/security-best-practices/SKILL.md` |
| XSS, CSRF, injection, SQL injection, hujum, exploit | `web-security-testing` + `owasp-top-10` | `~/.agents/skills/web-security-testing/SKILL.md` |
| input, validatsiya, sanitizatsiya, tozalash, foydalanuvchi kiritishi | `input-validation-sanitization-auditor` | `~/.agents/skills/input-validation-sanitization-auditor/SKILL.md` |
| OWASP, zaiflik auditi, penetration, xavfsizlik auditi | `owasp-top-10` | `~/.agents/skills/owasp-top-10/SKILL.md` |

---

#### 🚀 DEPLOY & INFRA

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| deploy, Docker, server, production, CI/CD, hosting, container | `docker-deployment` | `~/.agents/skills/docker-deployment/SKILL.md` |

---

#### ✍️ KONTENT & MARKETING

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| matn yozish, kopy, marketing, landing page, CTA, headline | `copywriting` | `.agents/skills/copywriting/SKILL.md` |
| matn tuzatish, grammatika, tahrir, editing, imlo, xato | `copy-editing` | `~/.agents/skills/copy-editing/SKILL.md` |
| psixologiya, mental model, persuasion, konversiya, nudge | `marketing-psychology` | `.agents/skills/marketing-psychology/SKILL.md` |
| SEO, meta, Google, qidiruv, indexing, sitemap, robots | `seo-audit` | `.agents/skills/seo-audit/SKILL.md` |
| programmatic SEO, template sahifalar, pSEO, ko'p sahifa | `programmatic-seo` | `.agents/skills/programmatic-seo/SKILL.md` |

---

#### 🔧 UTILITIES

| Kalit so'zlar | Skill | Yo'l |
|---------------|-------|------|
| commit, git, versiya, push | `conventional-commits` | `.agents/skills/conventional-commits/SKILL.md` |
| skill izla, topish, qanday qilaman, yangi skill | `find-skills` | `.agents/skills/find-skills/SKILL.md` |

---

### 3-qadam: Mos skill'larni O'QI

Aniqlangan **barcha** mos skill'larning `SKILL.md` fayllarini `view_file` tool bilan o'qi.

**Tartib:**
1. Avval **KRITIK** skill'larni o'qi (agar kerak bo'lsa)
2. Keyin **asosiy** vazifaga tegishli skill'larni o'qi
3. Oxirida **qo'shimcha** (yordamchi) skill'larni o'qi

> ⚠️ Agar skill fayli topilmasa — xato bermay, tashlab ket va keyingi skill'ga o't.

---

### 4-qadam: MAJBURIY — Foydalanuvchiga xabar ber

Ish boshlashdan **OLDIN** quyidagi formatda yoz:

```
🔧 Skill'lar aniqlandi va o'qildi:
  ✅ skill-nomi — sabab (loyiha / global)
  ✅ skill-nomi — sabab (loyiha / global)

📋 Ish rejasi:
  1. Birinchi qadam
  2. Ikkinchi qadam
  ...
```

**⛔ Bu blokni HECH QACHON tashlab ketma!** Foydalanuvchi shu orqali skill tizimi ishlayotganini tekshiradi.

---

### 5-qadam: Skill ko'rsatmalariga amal qilib ishla

Har bir o'qilgan skill'ning ko'rsatmalariga **to'liq** amal qil. Skill'lar bir-biriga zid kelsa — **loyiha skill'lari ustunlik** oladi.

---

## 📐 Skill zanjiri (chaining) qoidalari

Ba'zi vazifalar ketma-ket bir nechta skill talab qiladi:

| Vazifa turi | Skill zanjiri |
|-------------|---------------|
| Yangi feature yaratish | `brainstorming` → `writing-plans` → `executing-plans` → `verification-before-completion` |
| Bug tuzatish | `systematic-debugging` → `test-driven-development` → `verification-before-completion` |
| Xavfsizlik auditi | `owasp-top-10` → `security-best-practices` → `web-security-testing` → `input-validation-sanitization-auditor` |
| Deploy qilish | `docker-deployment` → `verification-before-completion` |
| Database o'zgarishi | `prisma-database-setup` → `prisma-cli` → `verification-before-completion` |
| PR yaratish | `requesting-code-review` → `conventional-commits` |

---

## 🚫 Qo'shimcha qoidalar

1. **Bir nechta skill mos kelsa** — hammasini o'qi, lekin asosiy vazifaga tegishlisini birinchi o'qi
2. **Hech biri mos kelmasa** — shunday yoz: `🔧 Skill'lar: maxsus skill kerak emas, umumiy bilim bilan ishlayman.`
3. **Commit qilishdan oldin** — `conventional-commits` skill'ini **har doim** o'qi
4. **Ishni tugatishdan oldin** — `verification-before-completion` skill'ini **har doim** o'qi
5. **O'zbek tilida** muloqot qil — foydalanuvchi o'zbek tilida yozadi
6. **Skill yo'l topilmasa** — xato berma, log qoldir va davom et
