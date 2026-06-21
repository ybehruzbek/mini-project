import os
import logging
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase URL yoki KEY topilmadi. .env faylini tekshiring.")

supabase: Client = create_client(url, key)

def init_db():
    # Supabase'da jadvallar SQL orqali yaratiladi, shuning uchun bu yerda hech nima qilmaymiz.
    pass

def save_user_data(user_id, data):
    """Foydalanuvchi ma'lumotlarini saqlash (upsert)"""
    user_data = {
        "user_id": user_id,
        "full_name": data.get('full_name'),
        "age": data.get('age'),
        "habit_level": data.get('habit_level'),
        "city": data.get('city', 'Toshkent'),
        "timezone": data.get('timezone', 'Asia/Tashkent'),
        "prayer_notifications": data.get('prayer_notifications', True),
    }
    
    supabase.table("users").upsert(user_data).execute()

def get_user(user_id):
    """Foydalanuvchi ma'lumotlarini olish"""
    response = supabase.table("users").select("full_name").eq("user_id", user_id).execute()
    if response.data and len(response.data) > 0:
        return (response.data[0]['full_name'],)
    return None

def get_user_full(user_id):
    """Foydalanuvchining to'liq ma'lumotlarini olish"""
    response = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None

def add_default_dhikr(user_id, habit_level):
    """Standart zikrlarni qo'shish"""
    daily_tgt = 33 if habit_level == 'beginner' else 100
    global_tgt = 40000
    
    dhikrs = [
        "Astagʻfirullahil aʼziym va atubi ilayh",
        "Hasbunallohu va ni'mal vakil",
        "Ya Malikul Mulk"
    ]
    
    for title in dhikrs:
        exists = supabase.table("dhikrs").select("id").eq("user_id", user_id).eq("title", title).execute()
        if not exists.data or len(exists.data) == 0:
            supabase.table("dhikrs").insert({
                "user_id": user_id,
                "title": title,
                "daily_target": daily_tgt,
                "global_target": global_tgt,
                "daily_count": 0,
                "global_count": 0
            }).execute()

def add_default_duas(user_id):
    """Standart duolarni foydalanuvchiga qo'shish"""
    from duas_data import get_all_default_duas
    
    defaults = get_all_default_duas()
    for dua in defaults:
        # Tekshiramiz allaqachon bormi
        exists = supabase.table("duas").select("id").eq("user_id", user_id).eq("text", dua["text"]).execute()
        if not exists.data or len(exists.data) == 0:
            supabase.table("duas").insert({
                "user_id": user_id,
                "text": dua["text"],
                "arabic": dua.get("arabic", ""),
                "category": dua["category"],
                "is_active": True
            }).execute()

def get_user_duas(user_id, category=None):
    """Foydalanuvchi duolarini olish"""
    query = supabase.table("duas").select("*").eq("user_id", user_id)
    if category:
        query = query.eq("category", category)
    response = query.order("category").order("id").execute()
    return response.data if response.data else []

def get_active_duas(user_id, category):
    """Foydalanuvchining faol duolarini kategoriya bo'yicha olish"""
    response = (supabase.table("duas")
                .select("*")
                .eq("user_id", user_id)
                .eq("category", category)
                .eq("is_active", True)
                .execute())
    return response.data if response.data else []

def toggle_dua(dua_id, is_active):
    """Duo faolligini o'zgartirish"""
    supabase.table("duas").update({"is_active": is_active}).eq("id", dua_id).execute()

def delete_dua(dua_id):
    """Duo o'chirish"""
    supabase.table("duas").delete().eq("id", dua_id).execute()

def add_custom_dua(user_id, text, category="custom"):
    """Yangi maxsus duo qo'shish"""
    supabase.table("duas").insert({
        "user_id": user_id,
        "text": text,
        "arabic": "",
        "category": category,
        "is_active": True
    }).execute()

# --- Namoz vaqtlari cache ---

def get_cached_prayer_times(city, date_str):
    """Cache'dan namoz vaqtlarini olish"""
    response = (supabase.table("prayer_cache")
                .select("*")
                .eq("city", city)
                .eq("date", date_str)
                .execute())
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None

def save_prayer_cache(city, date_str, times, notify_times):
    """Namoz vaqtlarini cache'ga saqlash"""
    data = {
        "city": city,
        "date": date_str,
        "fajr": times["fajr"],
        "dhuhr": times["dhuhr"],
        "asr": times["asr"],
        "maghrib": times["maghrib"],
        "isha": times["isha"],
        "fajr_notify": notify_times["fajr"],
        "dhuhr_notify": notify_times["dhuhr"],
        "asr_notify": notify_times["asr"],
        "maghrib_notify": notify_times["maghrib"],
        "isha_notify": notify_times["isha"],
    }
    
    try:
        supabase.table("prayer_cache").upsert(data, on_conflict="city,date").execute()
    except Exception as e:
        logger.error(f"Prayer cache saqlashda xatolik: {e}")

def get_users_by_city(city):
    """Berilgan shahardagi barcha foydalanuvchilarni olish"""
    response = (supabase.table("users")
                .select("user_id")
                .eq("city", city)
                .eq("prayer_notifications", True)
                .execute())
    return [u['user_id'] for u in response.data] if response.data else []

def get_all_active_cities():
    """Namoz eslatmalari faol bo'lgan barcha noyob shaharlarni olish"""
    response = (supabase.table("users")
                .select("city")
                .eq("prayer_notifications", True)
                .execute())
    if response.data:
        return list(set(u['city'] for u in response.data if u.get('city')))
    return []


if __name__ == "__main__":
    print("Supabase ulanishi tekshirilmoqda...")
    print(supabase.table("users").select("count", count="exact").execute())
