"""
Namoz vaqtlari moduli — Aladhan API orqali namoz vaqtlarini olish va cache qilish.
"""
import aiohttp
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# O'zbekiston shaharlari va koordinatalari
UZBEK_CITIES = {
    "Toshkent": (41.2995, 69.2401),
    "Samarqand": (39.6542, 66.9597),
    "Buxoro": (39.7681, 64.4556),
    "Andijon": (40.7821, 72.3442),
    "Namangan": (40.9983, 71.6726),
    "Farg'ona": (40.3834, 71.7870),
    "Nukus": (42.4628, 59.6003),
    "Qarshi": (38.8610, 65.8004),
    "Jizzax": (40.1158, 67.8422),
    "Urganch": (41.5533, 60.6236),
    "Navoiy": (40.1034, 65.3792),
    "Termiz": (37.2241, 67.2783),
    "Guliston": (40.4897, 68.7840),
    "Xiva": (41.3775, 60.3618),
    "Chirchiq": (41.4689, 69.5828),
    "Olmaliq": (40.8445, 69.5983),
    "Kokand": (40.5286, 70.9425),
    "Marg'ilon": (40.4700, 71.7200),
    "Shahrisabz": (39.0575, 66.8308),
}

# Namoz nomlari (API → O'zbek)
PRAYER_NAMES = {
    "fajr": "Bomdod",
    "dhuhr": "Peshin",
    "asr": "Asr",
    "maghrib": "Shom",
    "isha": "Xufton",
}

# Namoz eslatma emoji va matnlari
PRAYER_EMOJIS = {
    "fajr": "🌅",
    "dhuhr": "☀️",
    "asr": "🌤",
    "maghrib": "🌅",
    "isha": "🌙",
}


async def fetch_prayer_times(city_name: str, date: datetime = None) -> dict | None:
    """Aladhan API orqali namoz vaqtlarini olish.
    
    Args:
        city_name: Shahar nomi (UZBEK_CITIES dan)
        date: Sana (default: bugun)
    
    Returns:
        dict: {fajr, dhuhr, asr, maghrib, isha} — HH:MM formatda
        None: xatolik bo'lsa
    """
    if city_name not in UZBEK_CITIES:
        city_name = "Toshkent"
    
    lat, lon = UZBEK_CITIES[city_name]
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%d-%m-%Y")
    url = f"https://api.aladhan.com/v1/timings/{date_str}?latitude={lat}&longitude={lon}&method=3"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    timings = data["data"]["timings"]
                    return {
                        "fajr": timings["Fajr"][:5],
                        "dhuhr": timings["Dhuhr"][:5],
                        "asr": timings["Asr"][:5],
                        "maghrib": timings["Maghrib"][:5],
                        "isha": timings["Isha"][:5],
                    }
                else:
                    logger.error(f"Aladhan API xatosi: {resp.status}")
    except Exception as e:
        logger.error(f"Namoz vaqtlarini olishda xatolik ({city_name}): {e}")
    
    return None


def compute_notify_time(prayer_time_str: str, min_before: int = 10, max_before: int = 25) -> str:
    """Namoz vaqtidan 10-25 daqiqa oldingi random vaqtni hisoblash.
    
    Args:
        prayer_time_str: Namoz vaqti (HH:MM)
        min_before: Minimal daqiqa oldin
        max_before: Maksimal daqiqa oldin
    
    Returns:
        str: Eslatma vaqti (HH:MM)
    """
    h, m = map(int, prayer_time_str.split(":"))
    prayer_dt = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
    offset = random.randint(min_before, max_before)
    notify_dt = prayer_dt - timedelta(minutes=offset)
    return notify_dt.strftime("%H:%M")


def get_city_list() -> list[str]:
    """Shaharlar ro'yxatini qaytarish"""
    return sorted(UZBEK_CITIES.keys())


def format_prayer_times_message(times: dict, city: str) -> str:
    """Namoz vaqtlarini chiroyli formatda ko'rsatish"""
    if not times:
        return f"🕌 {city} uchun namoz vaqtlari topilmadi."
    
    today = datetime.now().strftime("%d.%m.%Y")
    text = (
        f"🕌 <b>{city} — Namoz Vaqtlari</b>\n"
        f"📅 {today}\n\n"
    )
    
    for key, uz_name in PRAYER_NAMES.items():
        emoji = PRAYER_EMOJIS.get(key, "🕐")
        time_str = times.get(key, "--:--")
        text += f"{emoji} <b>{uz_name}:</b> {time_str}\n"
    
    return text
