"""
Duo'lar ma'lumotlari — default duolar to'plami.
Har bir duo: arabic (arab yozuvi), text (lotin transliteratsiya), meaning (o'zbek ma'nosi)
"""
import random

# Tonggi duolar — Bomdod namozidan oldin/keyin yuboriladigan
MORNING_DUAS = [
    {
        "arabic": "اَلْحَمْدُ لِلّٰهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ",
        "text": "Alhamdu lillahillazi ahyana ba'da ma amatana va ilayhin nushur",
        "meaning": "Bizni (uyqu bilan) o'ldirganidan so'ng tiriltirgan Allohga hamd bo'lsin. Qaytish faqat Ungadir!"
    },
    {
        "arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلّٰهِ وَالْحَمْدُ لِلّٰهِ",
        "text": "Asbahna va asbahal mulku lillahi val hamdu lillah",
        "meaning": "Biz ham, mulk ham Allohga tegishli holda tongladi. Hamd Allohga!"
    },
    {
        "arabic": "اَللّٰهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ النُّشُورُ",
        "text": "Allohumma bika asbahna va bika amsayna va bika nahya va bika namutu va ilaykan nushur",
        "meaning": "Allohim, Sen bilan tonglashimiz va kechlashimiz, Sen bilan tirik bo'lishimiz va o'lishimiz. Qaytish Sengadir!"
    },
    {
        "arabic": "اَللّٰهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ هٰذَا الْيَوْمِ",
        "text": "Allohumma inni as'aluka xayra hazal yavm",
        "meaning": "Allohim, Sendan bu kunning yaxshiligini so'rayman!"
    },
    {
        "arabic": "سُبْحَانَ اللّٰهِ وَبِحَمْدِهِ",
        "text": "Subhanallahi va bihamdihi (100 marta)",
        "meaning": "Allohni poklab yod etaman va Unga hamd aytaman. (Kim buni ertalab 100 marta aytsa, uning gunohlari kechiriladi)"
    },
]

# Kechki duolar — Shom/Xufton namozidan oldin/keyin yuboriladigan
EVENING_DUAS = [
    {
        "arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلّٰهِ وَالْحَمْدُ لِلّٰهِ",
        "text": "Amsayna va amsal mulku lillahi val hamdu lillah",
        "meaning": "Biz ham, mulk ham Allohga tegishli holda kechladi. Hamd Allohga!"
    },
    {
        "arabic": "أَعُوذُ بِكَلِمَاتِ اللّٰهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ",
        "text": "A'uzu bi kalimatillahit tammati min sharri ma xalaq",
        "meaning": "Allohning mukammal so'zlari bilan yaratilgan narsalarning yomonligidan panoh tilayman!"
    },
    {
        "arabic": "اَللّٰهُمَّ بِكَ أَمْسَيْنَا وَبِكَ أَصْبَحْنَا وَبِكَ نَحْيَا وَبِكَ نَمُوتُ وَإِلَيْكَ الْمَصِيرُ",
        "text": "Allohumma bika amsayna va bika asbahna va bika nahya va bika namutu va ilaykal masir",
        "meaning": "Allohim, Sen bilan kechlashimiz va tonglashimiz, Sen bilan tirik bo'lishimiz va o'lishimiz. Qaytish Sengadir!"
    },
    {
        "arabic": "اَللّٰهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحُزْنِ",
        "text": "Allohumma inni a'uzu bika minal hammi val huzn",
        "meaning": "Allohim, g'am va qayg'udan Senga sig'inaman!"
    },
]

# Namoz oldidan o'qiladigan duolar
PRE_PRAYER_DUAS = [
    {
        "arabic": "اَللّٰهُمَّ اجْعَلْنِي مِنَ التَّوَّابِينَ وَاجْعَلْنِي مِنَ الْمُتَطَهِّرِينَ",
        "text": "Allohummaj'alni minat tavvabin vaj'alni minal mutatahhirin",
        "meaning": "Allohim, meni tavba qiluvchilardan va poklanuvchilardan qilgin!"
    },
    {
        "arabic": "سُبْحَانَكَ اللّٰهُمَّ وَبِحَمْدِكَ وَتَبَارَكَ اسْمُكَ وَتَعَالَى جَدُّكَ وَلَا إِلٰهَ غَيْرُكَ",
        "text": "Subhanakallohumma va bihamdika va tabarakasmuka va ta'ala jadduka va la ilaha g'ayruk",
        "meaning": "Allohim, Seni poklab yod etaman. Hamd Sengadir. Isming barakali. Ulug'vorliging buyukdir. Sendan o'zga iloh yo'q!"
    },
    {
        "arabic": "اَللّٰهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ",
        "text": "Allohumma salli ala Muhammadin va ala ali Muhammad",
        "meaning": "Allohim, Muhammad (s.a.v.)ga va u Zotning oilalariga rahmat yubor!"
    },
]

# Uxlashdan oldingi duolar
BEDTIME_DUAS = [
    {
        "arabic": "اَللّٰهُمَّ بِاسْمِكَ أَمُوتُ وَأَحْيَا",
        "text": "Allohumma bismika amutu va ahya",
        "meaning": "Allohim, Sening isming bilan o'laman va tirilaman!"
    },
    {
        "arabic": "بِاسْمِكَ رَبِّي وَضَعْتُ جَنْبِي وَبِكَ أَرْفَعُهُ",
        "text": "Bismika Rabbi vada'tu janbi va bika arfa'uhu",
        "meaning": "Robbim, Sening isming bilan yondim va Sening isming bilan turaman!"
    },
    {
        "arabic": "قُلْ هُوَ اللّٰهُ أَحَدٌ ١ اَللّٰهُ الصَّمَدُ ٢",
        "text": "Qul huvallahu ahad. Allahus samad... (Ixlos surasi — 3 marta o'qing)",
        "meaning": "Ayt: \"U Alloh yagonadir. Alloh behojatdir (hamma Unga muhtoj)...\" — Uxlashdan oldin 3 marta o'qing"
    },
]

# Umumiy duolar (kunning istalgan vaqtida)
GENERAL_DUAS = [
    {
        "arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        "text": "Rabbana atina fid dunya hasanatan va fil axirati hasanatan va qina azaban nar",
        "meaning": "Robbimiz, bizga dunyoda yaxshilik ber, oxiratda ham yaxshilik ber va bizni do'zax azobidan saqla!"
    },
    {
        "arabic": "حَسْبُنَا اللّٰهُ وَنِعْمَ الْوَكِيلُ",
        "text": "Hasbunallohu va ni'mal vakil",
        "meaning": "Bizga Alloh yetarlidir. U qanday go'zal himoyachidir!"
    },
    {
        "arabic": "لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللّٰهِ",
        "text": "La havla va la quvvata illa billah",
        "meaning": "Allohdan boshqa hech kimda kuch va quvvat yo'q!"
    },
]


def get_random_dua(category: str) -> dict:
    """Kategoriyaga qarab random duo olish.
    
    Args:
        category: 'morning', 'evening', 'pre_prayer', 'bedtime', 'general'
    
    Returns:
        dict: {arabic, text, meaning}
    """
    duas_map = {
        "morning": MORNING_DUAS,
        "evening": EVENING_DUAS,
        "pre_prayer": PRE_PRAYER_DUAS,
        "bedtime": BEDTIME_DUAS,
        "general": GENERAL_DUAS,
    }
    
    duas = duas_map.get(category, GENERAL_DUAS)
    return random.choice(duas)


def get_prayer_dua_category(prayer_key: str) -> str:
    """Namoz turiga qarab duo kategoriyasini aniqlash.
    
    Args:
        prayer_key: 'fajr', 'dhuhr', 'asr', 'maghrib', 'isha'
    
    Returns:
        str: duo kategoriyasi
    """
    mapping = {
        "fajr": "morning",
        "dhuhr": "pre_prayer",
        "asr": "pre_prayer",
        "maghrib": "evening",
        "isha": "bedtime",
    }
    return mapping.get(prayer_key, "general")


def format_dua_message(dua: dict, include_arabic: bool = True) -> str:
    """Duoni chiroyli formatda ko'rsatish."""
    text = ""
    if include_arabic and dua.get("arabic"):
        text += f"<blockquote>{dua['arabic']}</blockquote>\n\n"
    
    text += f"📖 <i>{dua['text']}</i>\n\n"
    
    if dua.get("meaning"):
        text += f"💡 <b>Ma'nosi:</b> {dua['meaning']}"
    
    return text


def get_all_default_duas() -> list[dict]:
    """Barcha default duolarni kategoriyalari bilan qaytarish (DB ga saqlash uchun)"""
    result = []
    
    for dua in MORNING_DUAS:
        result.append({**dua, "category": "morning"})
    for dua in EVENING_DUAS:
        result.append({**dua, "category": "evening"})
    for dua in PRE_PRAYER_DUAS:
        result.append({**dua, "category": "pre_prayer"})
    for dua in BEDTIME_DUAS:
        result.append({**dua, "category": "bedtime"})
    for dua in GENERAL_DUAS:
        result.append({**dua, "category": "general"})
    
    return result
