"""
Zikr va Duo — qoidalar, odob-axloq va tugatgandan keyingi yo'riqnomalar.
"""


# ==========================================
# --- Zikr tugatgandan keyin ko'rsatiladigan xabar ---
# ==========================================

POST_DHIKR_GUIDANCE = """
🎉 <b>Mashaa'Alloh! Zikrni tugatdingiz!</b>

📿 <b>{title}</b> — bugun <b>{count}</b> marta o'qildi
━━━━━━━━━━━━━━━━━━

🤲 <b>Endi nima qilish kerak:</b>

1️⃣ Qo'llaringizni ko'tarib duo qiling
2️⃣ Salavot ayting:
   <blockquote>Allohumma salli ala Muhammadin va ala ali Muhammad</blockquote>
3️⃣ Allohdan xohlaganingizni so'rang
4️⃣ Yuzingizga suring

💡 <b>Duo qoidalari:</b>
• Avval Allohga hamd ayting
• Payg'ambarimizga salavot ayting
• Keyin duoyingizni qiling
• Yana salavot bilan yakunlang

<i>"Meni eslanglar, Men ham sizlarni eslayman"</i>
— <b>Al-Baqara, 152</b>
"""

POST_DHIKR_GUIDANCE_SHORT = """
✅ <b>{title}</b> — <b>{count}</b> marta

🤲 Endi qo'l ko'tarib duo qiling:
1. Salavot ayting
2. Allohdan so'rang
3. Yuzingizga suring

<i>Alloh taolo qabul qilsin!</i> 🤲
"""


# ==========================================
# --- Zikr o'qish qoidalari ---
# ==========================================

DHIKR_RULES = """
📋 <b>Zikr o'qish odobi va qoidalari</b>
━━━━━━━━━━━━━━━━━━

🕌 <b>Tahorat:</b>
Tahoratli holda zikr o'qish afzalroq.
Lekin tahoratsiz ham zikr aytish mumkin.

🧭 <b>Yo'nalish:</b>
Qiblaga yuzlanib o'tirish mustahabdir.

🤫 <b>Ovoz:</b>
Past yoki o'rtacha ovozda, diqqat bilan.

📖 <b>Boshlash tartibi:</b>
1. <i>"A'uzu billahi minash shaytanir rajim"</i>
2. <i>"Bismillahir rohmanir rohiym"</i>
3. Zikrni o'qish
4. Duo qilish
5. Salavot bilan yakunlash

⏰ <b>Eng fazilatli vaqtlar:</b>
• Bomdod namozidan keyin 🌅
• Shom namozidan keyin 🌆
• Tunning oxirgi 1/3 qismi 🌙

⚠️ <b>Eslatma:</b>
Zikr paytida gaplashmaslik va diqqatni jamlash lozim.
Zikr ma'nosini tushunib, qalbdan aytish muhim.

💎 <b>Hadis:</b>
<blockquote>"Tilining zikrullohdan qurimagan kishiga baxtiyor bo'lganiga ishora qilinadi"
— Termiziy rivoyati</blockquote>
"""


# ==========================================
# --- Duo kategoriyalari qoidalari ---
# ==========================================

DUA_CATEGORY_RULES = {
    "morning": """
📋 <b>Tonggi duolar odobi</b>
━━━━━━━━━━━━━━━━━━

⏰ <b>Qachon o'qiladi:</b>
Bomdod namozidan KEYIN, quyosh chiqqunga qadar.
Bu vaqtda duo qabul bo'lish ehtimoli yuqori!

🕌 <b>Tayyorgarlik:</b>
• Tahoratli bo'lish
• Qiblaga yuzlanish
• Namoz o'rnida o'tirib qolish

📖 <b>Tartib:</b>
1. Uyg'onganda <i>"Alhamdu lillah"</i> aytish
2. Tahorat olish
3. Bomdod namozini o'qish
4. Namoz joyida qolib tonggi duolarni o'qish

💎 <b>Hadis:</b>
<blockquote>"Kim bomdod namozini jamoat bilan o'qib, quyosh chiqqunga qadar zikr qilib o'tirsa, so'ng ikki rak'at namoz o'qisa — buning uchun to'liq haj va umra savobidek savob bor."
— Termiziy rivoyati</blockquote>
""",

    "evening": """
📋 <b>Kechki duolar odobi</b>
━━━━━━━━━━━━━━━━━━

⏰ <b>Qachon:</b>
Shom namozidan KEYIN yoki uxlashdan OLDIN.

🕌 <b>Tayyorgarlik:</b>
Tahoratli bo'lish tavsiya etiladi.

📖 <b>Tartib:</b>
1. Shom namozini o'qish
2. Kechki duolarni o'qish
3. Vitr namozini o'qish

💎 <b>Hadis:</b>
<blockquote>"Kim kechqurun 3 marta Ixlos, Falaq, Nos suralarini o'qisa, Alloh uni har bir yomonlikdan saqlaydi."
— Abu Dovud rivoyati</blockquote>
""",

    "pre_prayer": """
📋 <b>Namoz oldidan o'qiladigan duolar</b>
━━━━━━━━━━━━━━━━━━

⏰ <b>Qachon:</b>
Azon va iqomat orasida.

🕌 <b>Tayyorgarlik:</b>
Tahorat olganingizdan keyin, namoz boshlanishini kutib turganingizda.

📖 <b>Tartib:</b>
1. Tahorat olish
2. Azonga javob berish
3. Duolarni o'qish
4. Namozga turish

💎 <b>Hadis:</b>
<blockquote>"Azon va iqomat orasidagi duo rad etilmaydi."
— Abu Dovud rivoyati</blockquote>
""",

    "bedtime": """
📋 <b>Uxlashdan oldingi duolar</b>
━━━━━━━━━━━━━━━━━━

⏰ <b>Qachon:</b>
Yotishdan OLDIN, to'shakka yotganingizda.

🕌 <b>Tayyorgarlik:</b>
• Tahorat olish (sunnati)
• O'ng tomoniga yotish
• O'ng qo'lini yonog'ining ostiga qo'yish

📖 <b>Tartib:</b>
1. Oyatul Kursiy o'qish
2. Ixlos, Falaq, Nos suralarini 3 martadan o'qish
3. Kaftlariga puflab badaniga surish
4. Uxlash duosini o'qish

💎 <b>Hadis:</b>
<blockquote>"Kim Oyatul Kursiyni uxlashdan oldin o'qisa, Alloh tomon bir muhofiz tayinlanadi va tongga qadar shayton yaqinlashmaydi."
— Buxoriy rivoyati</blockquote>
""",

    "general": """
📋 <b>Umumiy duolar odobi</b>
━━━━━━━━━━━━━━━━━━

⏰ <b>Qachon:</b>
Kunning istalgan vaqtida o'qilishi mumkin.

📖 <b>Eng yaxshi duo vaqtlari:</b>
• Sajda paytida
• Farz namozlardan keyin
• Juma kuni
• Kechning oxirgi uchdan bir qismi
• Yomg'ir yog'ayotgan paytda
• Azon va iqomat orasida

💎 <b>Hadis:</b>
<blockquote>"Banda Robbiga eng yaqin bo'lgan holati — sajda holatidir. Shu paytda ko'proq duo qilinglar."
— Muslim rivoyati</blockquote>
""",

    "custom": """
📋 <b>Shaxsiy duolar</b>
━━━━━━━━━━━━━━━━━━

Bu siz qo'shgan shaxsiy duolaringiz.

💡 <b>Maslahat:</b>
• Duo'ni arabcha bilsangiz aytib, keyin o'zbekchada so'rang
• Duo qilishdan oldin salavot ayting
• Yakunida ham salavot bilan tugating
• Duo paytida ishonch bilan so'rang
"""
}


def get_dua_rules(category: str) -> str:
    """Kategoriyaga mos duo qoidalarini olish"""
    return DUA_CATEGORY_RULES.get(category, DUA_CATEGORY_RULES["general"])
