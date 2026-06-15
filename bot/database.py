import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

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
    # Upsert foydalanuvchi
    user_data = {
        "user_id": user_id,
        "full_name": data.get('full_name'),
        "age": data.get('age'),
        "habit_level": data.get('habit_level')
    }
    # gender va timezone, streak_days lar hozircha olib tashlandi, kerak bo'lsa qo'shish mumkin
    
    supabase.table("users").upsert(user_data).execute()

def get_user(user_id):
    response = supabase.table("users").select("full_name").eq("user_id", user_id).execute()
    if response.data and len(response.data) > 0:
        return (response.data[0]['full_name'],)
    return None

def add_default_dhikr(user_id, habit_level):
    daily_tgt = 33 if habit_level == 'beginner' else 100
    global_tgt = 40000
    
    dhikrs = [
        "Astagʻfirullahil aʼziym va atubi ilayh",
        "Hasbunallohu va ni'mal vakil",
        "Ya Malikul Mulk"
    ]
    
    for title in dhikrs:
        # Tekshiramiz bormi yoqmi
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

if __name__ == "__main__":
    print("Supabase ulanishi tekshirilmoqda...")
    print(supabase.table("users").select("count", count="exact").execute())
