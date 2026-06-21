import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import math
import random
from dotenv import load_dotenv
from database import (
    init_db, save_user_data, add_default_dhikr, get_user, get_user_full,
    supabase, add_default_duas, get_user_duas, get_active_duas,
    toggle_dua, delete_dua, add_custom_dua, update_dua, get_dua_by_id,
    get_cached_prayer_times, save_prayer_cache, get_users_by_city, get_all_active_cities
)
from prayer import (
    UZBEK_CITIES, PRAYER_NAMES, PRAYER_EMOJIS,
    fetch_prayer_times, compute_notify_time, format_prayer_times_message
)
from duas_data import (
    get_random_dua, get_prayer_dua_category, format_dua_message,
    MORNING_DUAS, EVENING_DUAS
)

ADMIN_ID = 1277687464

# Muhit o'zgaruvchilarini yuklash
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Web App URL
WEB_APP_URL = "https://ybehruzbek.github.io/mini-project/frontend/?v=10"

# ==========================================
# --- FSM States ---
# ==========================================

class Onboarding(StatesGroup):
    name = State()
    age = State()
    gender = State()
    habit = State()
    city = State()

class CustomDhikr(StatesGroup):
    title = State()
    daily_target = State()
    global_target = State()

class EditDhikr(StatesGroup):
    dhikr_id = State()
    daily_target = State()
    global_target = State()

class LogDhikr(StatesGroup):
    custom_amount = State()

class SettingsState(StatesGroup):
    change_name = State()
    change_city = State()

class DuaState(StatesGroup):
    text = State()
    arabic = State()
    category = State()

class EditDuaState(StatesGroup):
    dua_id = State()
    arabic = State()
    text = State()


# ==========================================
# --- Keyboard Helpers ---
# ==========================================

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")],
        [InlineKeyboardButton(text="📿 Elektron Tasbeh (Web)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🤲 Zikrlarni ko'rish", callback_data="view_dhikrs")],
        [InlineKeyboardButton(text="🕌 Duo'lar", callback_data="view_duas")],
        [InlineKeyboardButton(text="📊 Mening statistikam", callback_data="view_stats")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")]
    ])

def get_daily_target_keyboard(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="33 ta", callback_data=f"{prefix}_daily_33"),
            InlineKeyboardButton(text="100 ta", callback_data=f"{prefix}_daily_100")
        ],
        [
            InlineKeyboardButton(text="500 ta", callback_data=f"{prefix}_daily_500"),
            InlineKeyboardButton(text="1000 ta", callback_data=f"{prefix}_daily_1000")
        ],
        [InlineKeyboardButton(text="✍️ O'zim yozaman", callback_data=f"{prefix}_daily_manual")]
    ])

def get_global_target_keyboard(prefix):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="10,000 ta", callback_data=f"{prefix}_global_10000"),
            InlineKeyboardButton(text="40,000 ta", callback_data=f"{prefix}_global_40000")
        ],
        [
            InlineKeyboardButton(text="100,000 ta", callback_data=f"{prefix}_global_100000"),
            InlineKeyboardButton(text="1,000,000 ta", callback_data=f"{prefix}_global_1000000")
        ],
        [InlineKeyboardButton(text="✍️ O'zim yozaman", callback_data=f"{prefix}_global_manual")]
    ])

def get_city_keyboard():
    """O'zbekiston shaharlari ro'yxati"""
    cities = sorted(UZBEK_CITIES.keys())
    keyboard = []
    row = []
    for city in cities:
        row.append(InlineKeyboardButton(text=city, callback_data=f"city_{city}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==========================================
# --- Web App Data Handler ---
# ==========================================

@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    """Web App (Elektron Tasbeh) dan kelgan ma'lumotlarni qabul qilish"""
    import json
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action')
        
        if action == 'save_dhikr':
            title = data.get('title', 'Zikr')
            count = data.get('count', 0)
            target = data.get('target', 0)
            
            if count >= target and target > 0:
                text = (
                    f"🎉 <b>Mashaa'Alloh!</b>\n\n"
                    f"📿 <b>{title}</b> — bugungi maqsadga yetdingiz!\n"
                    f"✅ Qilingan: <b>{count}</b> / {target}\n\n"
                    f"<i>Alloh taolo qabul qilsin! 🤲</i>"
                )
            else:
                text = (
                    f"✅ <b>Saqlandi!</b>\n\n"
                    f"📿 <b>{title}</b>\n"
                    f"📊 Bugungi holat: <b>{count}</b> / {target}\n\n"
                    f"<i>Davom eting, baraka topasiz inshaalloh! 🌿</i>"
                )
            
            await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Web App data xatosi: {e}")

# ==========================================
# --- Onboarding (Ro'yxatdan o'tish) ---
# ==========================================

@dp.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    user = get_user(message.from_user.id)
    if user:
        name = user[0]
        await message.answer(
            f"Assalomu alaykum yana bir bor, hurmatli {name}! 🌙\n\n"
            "«Qalb Taskini» botiga xush kelibsiz. Zikrlarni davom ettirishingiz mumkin 👇",
            reply_markup=get_main_keyboard()
        )
        return

    first_name = message.from_user.first_name
    
    await message.answer(
        f"Assalomu alaykum, {first_name}! 🌙\n\n"
        "«Qalb Taskini» — ruhiy xotirjamlik va doimiy zikrda bo'lishingiz uchun yaratilgan shaxsiy yordamchingiz.\n\n"
        "Bu yerda siz o'z zikrlaringizni tartibga solishingiz, eslatmalar olishingiz va qulay elektron tasbehdan foydalanishingiz mumkin. 🌿"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Ha, '{first_name}' qolaversin", callback_data="use_tg_name")]
    ])
    
    await message.answer(
        f"Siz bilan yaqinroq tanishishim va botni aynan sizga moslashim uchun ismingiz kerak.\n\n"
        f"Sizga Telegramdagi ismingiz ({first_name}) bilan murojaat qilaymi yoki bu yerga o'zingiz boshqa ism yozasizmi?",
        reply_markup=keyboard
    )
    await state.set_state(Onboarding.name)

async def ask_for_age(target_message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 20 yoshgacha", callback_data="age_under20")],
        [InlineKeyboardButton(text="🌿 21-30 yosh", callback_data="age_21-30")],
        [InlineKeyboardButton(text="🌳 31-50 yosh", callback_data="age_31-50")],
        [InlineKeyboardButton(text="🏔 50 yoshdan yuqori", callback_data="age_over50")]
    ])
    await target_message.answer("Sizga moslashtirishim uchun, yosh oralig'ingizni belgilang:", reply_markup=keyboard)
    await state.set_state(Onboarding.age)

@dp.callback_query(StateFilter(Onboarding.name), F.data == "use_tg_name")
async def process_name_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(full_name=callback.from_user.first_name)
    await ask_for_age(callback.message, state)

@dp.message(StateFilter(Onboarding.name))
async def process_name_text(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await ask_for_age(message, state)

@dp.callback_query(StateFilter(Onboarding.age), F.data.startswith("age_"))
async def process_age(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    age_group = callback.data.split("_")[1]
    await state.update_data(age=age_group)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Erkak", callback_data="gender_male"),
         InlineKeyboardButton(text="👩 Ayol", callback_data="gender_female")]
    ])
    await callback.message.answer("Jinsingizni belgilang:", reply_markup=keyboard)
    await state.set_state(Onboarding.gender)

@dp.callback_query(StateFilter(Onboarding.gender), F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Yangi boshlayapman", callback_data="habit_beginner")],
        [InlineKeyboardButton(text="🌿 Vaqt topganda qilaman", callback_data="habit_medium")],
        [InlineKeyboardButton(text="🌳 Doimiy odatim bor", callback_data="habit_advanced")]
    ])
    await callback.message.answer("Kunlik zikr qilish odatingiz qanday?", reply_markup=keyboard)
    await state.set_state(Onboarding.habit)

@dp.callback_query(StateFilter(Onboarding.habit), F.data.startswith("habit_"))
async def process_habit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    habit = callback.data.split("_")[1]
    await state.update_data(habit_level=habit)
    
    # Shahar tanlash
    await callback.message.answer(
        "🌍 Namoz vaqtlarini to'g'ri hisoblashim uchun shahringizni tanlang:",
        reply_markup=get_city_keyboard()
    )
    await state.set_state(Onboarding.city)

@dp.callback_query(StateFilter(Onboarding.city), F.data.startswith("city_"))
async def process_city(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    city = callback.data[5:]  # "city_Toshkent" → "Toshkent"
    await state.update_data(city=city, timezone="Asia/Tashkent", prayer_notifications=True)
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    save_user_data(user_id, data)
    add_default_dhikr(user_id, data.get('habit_level', 'beginner'))
    add_default_duas(user_id)
    
    await state.clear()
    
    name = data.get('full_name', "Do'stim")
    
    await callback.message.answer(
        f"Rahmat, hurmatli {name}! Ma'lumotlaringiz muvaffaqiyatli saqlandi. ✅\n\n"
        f"📍 Shahringiz: <b>{city}</b>\n"
        f"🕌 Namoz eslatmalari faollashtirildi\n"
        f"🤲 Standart duolar qo'shildi\n\n"
        "Odatingizga mos ravishda kunlik zikrlarni belgilab qo'ydim.\n\n"
        "Quyidagi tugma orqali boshlaymiz 👇",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# ==========================================
# --- Zikrlarni boshqarish qismi ---
# ==========================================

def get_completion_msg(title, daily_tgt, global_tgt):
    if daily_tgt <= 0:
        return f"✅ <b>Maqsad saqlandi:</b>\n\n📿 {title}\nKunlik: {daily_tgt} ta | Umumiy: {global_tgt} ta"
    
    days = math.ceil(global_tgt / daily_tgt)
    months = ""
    if days > 30:
        m = days // 30
        d = days % 30
        months = f" (taxminan {m} oy-u {d} kun)"
        
    return (
        f"✅ <b>Maqsad muvaffaqiyatli saqlandi!</b>\n\n"
        f"<blockquote>📿 <b>{title}</b></blockquote>\n"
        f"📅 Kuniga: <b>{daily_tgt:,} marta</b>\n"
        f"🎯 Jami: <b>{global_tgt:,} marta</b>\n\n"
        f"Siz har kuni muntazam ravishda aytib borsangiz, <b>{days} kun{months}</b> ichida ushbu zikrni to'liq yakunlagan bo'lasiz inshaalloh! 🤲\n"
        f"<i>Men sizga belgilangan vaqtlarda eslatib turaman.</i> 🌿"
    )

def get_start_action_keyboard():
    hour = datetime.now().hour
    buttons = [[InlineKeyboardButton(text="Hozirroq boshlayman 🚀", callback_data="start_action_now")]]
    
    if 8 <= hour < 18:
        buttons.append([InlineKeyboardButton(text="1 soatdan so'ng ⏳", callback_data="start_action_1h")])
        buttons.append([InlineKeyboardButton(text="Kechqurun 🌙", callback_data="start_action_evening")])
    elif 18 <= hour < 22:
        buttons.append([InlineKeyboardButton(text="Uxlashdan oldin 🛏", callback_data="start_action_bedtime")])
        buttons.append([InlineKeyboardButton(text="Ertalabdan 🌅", callback_data="start_action_morning")])
    else:
        buttons.append([InlineKeyboardButton(text="Ertalabdan 🌅", callback_data="start_action_morning")])
        
    buttons.append([InlineKeyboardButton(text="⬅️ Zikrlar ro'yxati", callback_data="view_dhikrs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(F.data == "view_stats")
async def view_stats_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    today = datetime.now().strftime("%Y-%m-%d")
    prog_resp = supabase.table('daily_progress').select('count').eq('user_id', user_id).eq('date', today).execute()
    today_total = sum(p['count'] for p in prog_resp.data) if prog_resp.data else 0
    
    dhikr_resp = supabase.table('dhikrs').select('title, global_count').eq('user_id', user_id).execute()
    total_global = sum(d['global_count'] for d in dhikr_resp.data) if dhikr_resp.data else 0
    
    favorite = "Yo'q"
    if dhikr_resp.data:
        sorted_dhikrs = sorted(dhikr_resp.data, key=lambda x: x['global_count'], reverse=True)
        if sorted_dhikrs and sorted_dhikrs[0]['global_count'] > 0:
            favorite = f"{sorted_dhikrs[0]['title']} ({sorted_dhikrs[0]['global_count']} marta)"
            
    text = (
        "📊 <b>Sizning Statistikangiz</b>\n\n"
        f"🗓 <b>Bugungi natija:</b> {today_total} marta\n"
        f"🌐 <b>Umumiy o'qilgan:</b> {total_global} marta\n"
        f"🏆 <b>Sevimli zikringiz:</b> {favorite}\n\n"
        "<i>Batafsil grafikalar, ketma-ketlik (streak) va qiziqarli ma'lumotlarni ko'rish uchun <b>Web Ilovaga</b> kiring!</i>"
    )
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📿 Elektron Tasbeh (Web)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="main_menu")]
    ]), parse_mode="HTML")

@dp.callback_query(F.data == "view_dhikrs")
async def view_dhikrs_handler(callback: types.CallbackQuery):
    response = supabase.table('dhikrs').select('id, title, daily_target, global_target, global_count').eq('user_id', callback.from_user.id).execute()
    dhikrs = [(d['id'], d['title'], d['daily_target'], d['global_target'], d['global_count']) for d in response.data]
    
    text = "Sizning kundalik zikrlaringiz ro'yxati:\n\n"
    keyboard_buttons = []
    
    for idx, d in enumerate(dhikrs, 1):
        dhikr_id, title, daily_tgt, global_tgt, global_prog = d
        text += f"{idx}. 📿 {title}\nKunlik: {daily_tgt} ta | Umumiy maqsad: {global_tgt} ta\n\n"
        keyboard_buttons.append([InlineKeyboardButton(text=f"✏️ {idx}-zikrni tahrirlash", callback_data=f"edit_dhikr_{dhikr_id}")])
        
    keyboard_buttons.append([InlineKeyboardButton(text="➕ Yangi zikr qo'shish", callback_data="add_custom_dhikr")])
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    name = user[0] if user else "Do'stim"
    await callback.message.edit_text(
        f"Assalomu alaykum yana bir bor, hurmatli {name}! 🌙\n\n"
        "«Qalb Taskini» botiga xush kelibsiz. Zikrlarni davom ettirishingiz mumkin 👇",
        reply_markup=get_main_keyboard()
    )

# --- 1. Yangi Zikr Qo'shish FSM ---

@dp.callback_query(F.data == "add_custom_dhikr")
async def add_custom_dhikr_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Yangi zikringiz matnini yozing:\n(Masalan: Subhanalloh)")
    await state.set_state(CustomDhikr.title)

@dp.message(StateFilter(CustomDhikr.title))
async def process_custom_dhikr_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Ushbu zikr uchun KUNLIK maqsadingiz nechta bo'lishini xohlaysiz?",
        reply_markup=get_daily_target_keyboard("custom")
    )
    await state.set_state(CustomDhikr.daily_target)

@dp.callback_query(StateFilter(CustomDhikr.daily_target), F.data.startswith("custom_daily_"))
async def process_custom_daily_btn(callback: types.CallbackQuery, state: FSMContext):
    val = callback.data.split("_")[2]
    if val == "manual":
        await callback.message.edit_text("Iltimos, kunlik maqsadni raqamda yozing (masalan: 150):")
    else:
        await state.update_data(daily_target=int(val))
        await callback.message.edit_text(
            f"Kunlik maqsad: {val} ta ✅\n\nUshbu zikr uchun UMUMIY (katta) maqsadingiz nechta?",
            reply_markup=get_global_target_keyboard("custom")
        )
        await state.set_state(CustomDhikr.global_target)

@dp.message(StateFilter(CustomDhikr.daily_target))
async def process_custom_dhikr_daily_target_msg(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, maqsadni faqat raqamlar bilan kiriting.")
        return
        
    await state.update_data(daily_target=int(message.text))
    await message.answer(
        f"Kunlik maqsad: {message.text} ta ✅\n\nUshbu zikr uchun UMUMIY (katta) maqsadingiz nechta?",
        reply_markup=get_global_target_keyboard("custom")
    )
    await state.set_state(CustomDhikr.global_target)

@dp.callback_query(StateFilter(CustomDhikr.global_target), F.data.startswith("custom_global_"))
async def process_custom_global_btn(callback: types.CallbackQuery, state: FSMContext):
    val = callback.data.split("_")[2]
    if val == "manual":
        await callback.message.edit_text("Iltimos, umumiy maqsadni raqamda yozing (masalan: 70000):")
    else:
        data = await state.get_data()
        title = data['title']
        daily_tgt = data['daily_target']
        global_tgt = int(val)
        
        supabase.table('dhikrs').insert({
            'user_id': callback.from_user.id,
            'title': title,
            'daily_target': daily_tgt,
            'global_target': global_tgt,
            'daily_count': 0,
            'global_count': 0,
        }).execute()
                
        await state.clear()
        keyboard = get_start_action_keyboard()
        await callback.message.edit_text(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")


@dp.message(StateFilter(CustomDhikr.global_target))
async def process_custom_dhikr_global_target_msg(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, umumiy maqsadni faqat raqamlar bilan kiriting.")
        return
        
    data = await state.get_data()
    title = data['title']
    daily_tgt = data['daily_target']
    global_tgt = int(message.text)
    
    supabase.table('dhikrs').insert({
        'user_id': message.from_user.id,
        'title': title,
        'daily_target': daily_tgt,
        'global_target': global_tgt,
        'daily_count': 0,
        'global_count': 0,
    }).execute()
            
    await state.clear()
    
    keyboard = get_start_action_keyboard()
    await message.answer(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")


# --- 2. Zikrni Tahrirlash FSM ---

@dp.callback_query(F.data.startswith("edit_dhikr_"))
async def edit_dhikr_handler(callback: types.CallbackQuery, state: FSMContext):
    dhikr_id = int(callback.data.split("_")[2])
    
    response = supabase.table('dhikrs').select('title').eq('id', dhikr_id).execute()
    title = response.data[0]['title']
    
    await callback.message.edit_text(
        f"📿 {title}\n\nYangi KUNLIK maqsadni tanlang:",
        reply_markup=get_daily_target_keyboard("edit")
    )
    await state.set_state(EditDhikr.daily_target)
    await state.update_data(dhikr_id=dhikr_id)


@dp.callback_query(StateFilter(EditDhikr.daily_target), F.data.startswith("edit_daily_"))
async def process_edit_daily_btn(callback: types.CallbackQuery, state: FSMContext):
    val = callback.data.split("_")[2]
    if val == "manual":
        await callback.message.edit_text("Iltimos, yangi kunlik maqsadni raqamda yozing:")
    else:
        await state.update_data(daily_target=int(val))
        await callback.message.edit_text(
            f"Kunlik maqsad: {val} ta ✅\n\nEndi UMUMIY maqsadni tanlang:",
            reply_markup=get_global_target_keyboard("edit")
        )
        await state.set_state(EditDhikr.global_target)

@dp.message(StateFilter(EditDhikr.daily_target))
async def process_edit_dhikr_daily_msg(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
        
    await state.update_data(daily_target=int(message.text))
    await message.answer(
        f"Kunlik maqsad: {message.text} ta ✅\n\nEndi UMUMIY maqsadni tanlang:",
        reply_markup=get_global_target_keyboard("edit")
    )
    await state.set_state(EditDhikr.global_target)

@dp.callback_query(StateFilter(EditDhikr.global_target), F.data.startswith("edit_global_"))
async def process_edit_global_btn(callback: types.CallbackQuery, state: FSMContext):
    val = callback.data.split("_")[2]
    if val == "manual":
        await callback.message.edit_text("Iltimos, yangi umumiy maqsadni raqamda yozing:")
    else:
        data = await state.get_data()
        dhikr_id = data['dhikr_id']
        daily_tgt = data['daily_target']
        global_tgt = int(val)
        
        supabase.table('dhikrs').update({
            'daily_target': daily_tgt,
            'global_target': global_tgt
        }).eq('id', dhikr_id).execute()
                
        await state.clear()
        keyboard = get_start_action_keyboard()
        
        response = supabase.table('dhikrs').select('title').eq('id', dhikr_id).execute()
        title = response.data[0]['title']
        
        await callback.message.edit_text(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")


@dp.message(StateFilter(EditDhikr.global_target))
async def process_edit_dhikr_global_msg(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting.")
        return
        
    data = await state.get_data()
    dhikr_id = data['dhikr_id']
    daily_tgt = data['daily_target']
    global_tgt = int(message.text)
    
    supabase.table('dhikrs').update({
        'daily_target': daily_tgt,
        'global_target': global_tgt
    }).eq('id', dhikr_id).execute()
    
    title_resp = supabase.table('dhikrs').select('title').eq('id', dhikr_id).execute()
    title = title_resp.data[0]['title']
            
    await state.clear()
    
    keyboard = get_start_action_keyboard()
    await message.answer(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")


# ==========================================
# --- Duo'lar tizimi (Pagination) ---
# ==========================================

DUA_CATEGORY_NAMES = {
    "morning": "🌅 Tonggi duolar",
    "evening": "🌙 Kechki duolar",
    "pre_prayer": "🕌 Namoz oldidan",
    "bedtime": "🛏 Uxlashdan oldin",
    "general": "📿 Umumiy duolar",
    "custom": "✍️ Shaxsiy duolar",
}

DUA_CATEGORY_ORDER = ["morning", "evening", "pre_prayer", "bedtime", "general", "custom"]

def build_dua_card(duas, index, category):
    """Bitta duo'ni karta ko'rinishida yaratish"""
    total = len(duas)
    if total == 0:
        return None, None
    
    idx = index % total
    dua = duas[idx]
    cat_name = DUA_CATEGORY_NAMES.get(category, category)
    status = "✅ Faol" if dua.get('is_active', True) else "❌ Nofaol"
    
    text = f"{cat_name}  ({idx + 1} / {total})\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    # Arabcha matni
    arabic = dua.get('arabic', '')
    if arabic and arabic.strip():
        text += f"📜 <b>Arabcha:</b>\n<blockquote>{arabic}</blockquote>\n\n"
    
    # O'qilishi / Ma'nosi
    dua_text = dua.get('text', '')
    if dua_text:
        text += f"📝 <b>O'qilishi:</b>\n{dua_text}\n\n"
    
    text += f"Holati: {status}\n"
    
    # Keyboard
    buttons = []
    
    # Navigatsiya qatori
    nav_row = []
    if total > 1:
        prev_idx = (idx - 1) % total
        next_idx = (idx + 1) % total
        nav_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"dua_page_{category}_{prev_idx}"))
        nav_row.append(InlineKeyboardButton(text=f"{idx + 1}/{total}", callback_data="noop"))
        nav_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"dua_page_{category}_{next_idx}"))
    else:
        nav_row.append(InlineKeyboardButton(text=f"1/1", callback_data="noop"))
    buttons.append(nav_row)
    
    # Faollik toggle
    if dua.get('is_active', True):
        buttons.append([InlineKeyboardButton(text="❌ Web-appda yashirish", callback_data=f"dua_off_{category}_{idx}_{dua['id']}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Web-appda ko'rsatish", callback_data=f"dua_on_{category}_{idx}_{dua['id']}")])
    
    # Tahrirlash va o'chirish (faqat custom)
    action_row = []
    action_row.append(InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"dua_edit_{category}_{idx}_{dua['id']}"))
    if category == "custom":
        action_row.append(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"dua_del_{category}_{idx}_{dua['id']}"))
    buttons.append(action_row)
    
    # Orqaga
    buttons.append([InlineKeyboardButton(text="⬅️ Kategoriyalar", callback_data="view_duas")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, keyboard


@dp.callback_query(F.data == "view_duas")
async def view_duas_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    duas = get_user_duas(user_id)
    
    if not duas:
        add_default_duas(user_id)
        duas = get_user_duas(user_id)
    
    # Kategoriyalar bo'yicha guruhlash
    categories = {}
    for d in duas:
        cat = d.get('category', 'custom')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(d)
    
    text = "🤲 <b>Sizning Duo'laringiz</b>\n\n"
    
    total = len(duas)
    active = sum(1 for d in duas if d.get('is_active', True))
    text += f"📊 Jami: <b>{total}</b> ta duo | Faol: <b>{active}</b> ta\n\n"
    
    for cat_key in DUA_CATEGORY_ORDER:
        if cat_key in categories:
            cat_duas = categories[cat_key]
            cat_name = DUA_CATEGORY_NAMES.get(cat_key, cat_key)
            active_count = sum(1 for d in cat_duas if d.get('is_active', True))
            text += f"{cat_name}: <b>{active_count}</b>/{len(cat_duas)} ta\n"
    
    keyboard_buttons = []
    for cat_key in DUA_CATEGORY_ORDER:
        if cat_key in categories:
            cat_name = DUA_CATEGORY_NAMES.get(cat_key, cat_key)
            count = len(categories[cat_key])
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"{cat_name} ({count})",
                callback_data=f"dua_page_{cat_key}_0"
            )])
    
    keyboard_buttons.append([InlineKeyboardButton(text="➕ Yangi duo qo'shish", callback_data="add_custom_dua")])
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(F.data == "noop")
async def noop_handler(callback: types.CallbackQuery):
    await callback.answer()


@dp.callback_query(F.data.startswith("dua_page_"))
async def dua_page_handler(callback: types.CallbackQuery):
    """Duo kartasini ko'rsatish: dua_page_{category}_{index}"""
    parts = callback.data.split("_")
    # dua_page_morning_0 → ['dua', 'page', 'morning', '0']
    # dua_page_pre_prayer_0 → ['dua', 'page', 'pre', 'prayer', '0']
    category = "_".join(parts[2:-1])
    index = int(parts[-1])
    
    user_id = callback.from_user.id
    duas = get_user_duas(user_id, category)
    
    if not duas:
        cat_name = DUA_CATEGORY_NAMES.get(category, category)
        await callback.message.edit_text(
            f"{cat_name}\n\nBu kategoriyada hali duo yo'q.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Duo qo'shish", callback_data="add_custom_dua")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="view_duas")]
            ])
        )
        return
    
    text, keyboard = build_dua_card(duas, index, category)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# --- Toggle: Faol/Nofaol → kartaga qaytish ---

@dp.callback_query(F.data.startswith("dua_on_"))
async def dua_toggle_on_handler(callback: types.CallbackQuery):
    """dua_on_{category}_{index}_{dua_id}"""
    parts = callback.data.split("_")
    dua_id = int(parts[-1])
    index = int(parts[-2])
    category = "_".join(parts[2:-2])
    
    toggle_dua(dua_id, True)
    await callback.answer("✅ Duo faollashtirildi!")
    
    # Kartani qayta ko'rsatish
    user_id = callback.from_user.id
    duas = get_user_duas(user_id, category)
    text, keyboard = build_dua_card(duas, index, category)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(F.data.startswith("dua_off_"))
async def dua_toggle_off_handler(callback: types.CallbackQuery):
    """dua_off_{category}_{index}_{dua_id}"""
    parts = callback.data.split("_")
    dua_id = int(parts[-1])
    index = int(parts[-2])
    category = "_".join(parts[2:-2])
    
    toggle_dua(dua_id, False)
    await callback.answer("❌ Duo nofaol qilindi!")
    
    user_id = callback.from_user.id
    duas = get_user_duas(user_id, category)
    text, keyboard = build_dua_card(duas, index, category)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# --- Delete → kartaga qaytish ---

@dp.callback_query(F.data.startswith("dua_del_"))
async def dua_delete_handler(callback: types.CallbackQuery):
    """dua_del_{category}_{index}_{dua_id}"""
    parts = callback.data.split("_")
    dua_id = int(parts[-1])
    index = int(parts[-2])
    category = "_".join(parts[2:-2])
    
    delete_dua(dua_id)
    await callback.answer("🗑 Duo o'chirib tashlandi!")
    
    user_id = callback.from_user.id
    duas = get_user_duas(user_id, category)
    
    if not duas:
        await callback.message.edit_text(
            f"{DUA_CATEGORY_NAMES.get(category, category)}\n\nBu kategoriyada duo qolmadi.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Duo qo'shish", callback_data="add_custom_dua")],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="view_duas")]
            ])
        )
        return
    
    new_index = min(index, len(duas) - 1)
    text, keyboard = build_dua_card(duas, new_index, category)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# --- B-variant Tahrirlash (Bosqichma-bosqich: arabcha → ma'no) ---

@dp.callback_query(F.data.startswith("dua_edit_"))
async def dua_edit_start_handler(callback: types.CallbackQuery, state: FSMContext):
    """dua_edit_{category}_{index}_{dua_id}"""
    parts = callback.data.split("_")
    dua_id = int(parts[-1])
    index = int(parts[-2])
    category = "_".join(parts[2:-2])
    
    dua = get_dua_by_id(dua_id)
    if not dua:
        await callback.answer("Duo topilmadi!", show_alert=True)
        return
    
    await state.set_state(EditDuaState.arabic)
    await state.update_data(dua_id=dua_id, category=category, index=index)
    
    current_arabic = dua.get('arabic', '') or 'Kiritilmagan'
    
    await callback.message.edit_text(
        f"✏️ <b>Duo tahrirlash</b> (1/2)\n\n"
        f"Hozirgi arabcha:\n<blockquote>{current_arabic}</blockquote>\n\n"
        f"Yangi arabcha matnini yuboring.\n"
        f"Yoki o'zgartirishsiz qoldirish uchun /skip buyrug'ini bosing.",
        parse_mode="HTML"
    )


@dp.message(StateFilter(EditDuaState.arabic), Command("skip"))
async def edit_dua_skip_arabic(message: types.Message, state: FSMContext):
    """Arabchani o'tkazib yuborish"""
    data = await state.get_data()
    dua = get_dua_by_id(data['dua_id'])
    current_text = dua.get('text', '') if dua else 'Kiritilmagan'
    
    await state.set_state(EditDuaState.text)
    await message.answer(
        f"✏️ <b>Duo tahrirlash</b> (2/2)\n\n"
        f"Hozirgi o'qilishi:\n<blockquote>{current_text}</blockquote>\n\n"
        f"Yangi matnni yuboring yoki /skip bosing.",
        parse_mode="HTML"
    )


@dp.message(StateFilter(EditDuaState.arabic))
async def edit_dua_arabic(message: types.Message, state: FSMContext):
    """Yangi arabcha matnini qabul qilish"""
    await state.update_data(new_arabic=message.text)
    
    data = await state.get_data()
    dua = get_dua_by_id(data['dua_id'])
    current_text = dua.get('text', '') if dua else 'Kiritilmagan'
    
    await state.set_state(EditDuaState.text)
    await message.answer(
        f"✅ Arabcha yangilandi!\n\n"
        f"✏️ <b>Duo tahrirlash</b> (2/2)\n\n"
        f"Hozirgi o'qilishi:\n<blockquote>{current_text}</blockquote>\n\n"
        f"Yangi matnni yuboring yoki /skip bosing.",
        parse_mode="HTML"
    )


@dp.message(StateFilter(EditDuaState.text), Command("skip"))
async def edit_dua_skip_text(message: types.Message, state: FSMContext):
    """Ma'noni o'tkazib yuborish va saqlash"""
    data = await state.get_data()
    
    updates = {}
    if 'new_arabic' in data:
        updates['arabic'] = data['new_arabic']
    
    if updates:
        update_dua(data['dua_id'], updates)
    
    await state.clear()
    
    category = data.get('category', 'custom')
    index = data.get('index', 0)
    user_id = message.from_user.id
    duas = get_user_duas(user_id, category)
    
    text_msg, keyboard = build_dua_card(duas, index, category)
    await message.answer("✅ Duo yangilandi!\n\n" + text_msg, reply_markup=keyboard, parse_mode="HTML")


@dp.message(StateFilter(EditDuaState.text))
async def edit_dua_text(message: types.Message, state: FSMContext):
    """Yangi matnni qabul qilish va saqlash"""
    data = await state.get_data()
    
    updates = {'text': message.text}
    if 'new_arabic' in data:
        updates['arabic'] = data['new_arabic']
    
    update_dua(data['dua_id'], updates)
    await state.clear()
    
    category = data.get('category', 'custom')
    index = data.get('index', 0)
    user_id = message.from_user.id
    duas = get_user_duas(user_id, category)
    
    text_msg, keyboard = build_dua_card(duas, index, category)
    await message.answer("✅ Duo muvaffaqiyatli yangilandi!\n\n" + text_msg, reply_markup=keyboard, parse_mode="HTML")


# --- Yangi duo qo'shish (B-variant: arabcha → matn → kategoriya) ---

@dp.callback_query(F.data == "add_custom_dua")
async def add_custom_dua_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✍️ <b>Yangi duo qo'shish</b> (1/3)\n\n"
        "Duo'ning <b>arabcha</b> matnini yozing.\n"
        "Yoki arabchasi bo'lmasa /skip bosing.",
        parse_mode="HTML"
    )
    await state.set_state(DuaState.arabic)


@dp.message(StateFilter(DuaState.arabic), Command("skip"))
async def process_new_dua_skip_arabic(message: types.Message, state: FSMContext):
    await state.update_data(arabic="")
    await message.answer(
        "✍️ <b>Yangi duo qo'shish</b> (2/3)\n\n"
        "Duo'ning <b>o'qilishi yoki ma'nosini</b> yozing:\n\n"
        "<i>Masalan: Allohumma inni as'aluka al-jannah</i>",
        parse_mode="HTML"
    )
    await state.set_state(DuaState.text)


@dp.message(StateFilter(DuaState.arabic))
async def process_new_dua_arabic(message: types.Message, state: FSMContext):
    await state.update_data(arabic=message.text)
    await message.answer(
        "✅ Arabcha saqlandi!\n\n"
        "✍️ <b>Yangi duo qo'shish</b> (2/3)\n\n"
        "Endi duo'ning <b>o'qilishi yoki ma'nosini</b> yozing:",
        parse_mode="HTML"
    )
    await state.set_state(DuaState.text)


@dp.message(StateFilter(DuaState.text))
async def process_dua_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌅 Tonggi", callback_data="newdua_cat_morning"),
         InlineKeyboardButton(text="🌙 Kechki", callback_data="newdua_cat_evening")],
        [InlineKeyboardButton(text="🕌 Namoz oldidan", callback_data="newdua_cat_pre_prayer"),
         InlineKeyboardButton(text="🛏 Uxlashdan oldin", callback_data="newdua_cat_bedtime")],
        [InlineKeyboardButton(text="📿 Umumiy", callback_data="newdua_cat_general"),
         InlineKeyboardButton(text="✍️ Shaxsiy", callback_data="newdua_cat_custom")],
    ])
    
    await message.answer(
        "✍️ <b>Yangi duo qo'shish</b> (3/3)\n\n"
        "Bu duo qaysi kategoriyaga tegishli?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(DuaState.category)


@dp.callback_query(StateFilter(DuaState.category), F.data.startswith("newdua_cat_"))
async def process_dua_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data[11:]  # "newdua_cat_morning" → "morning"
    data = await state.get_data()
    
    add_custom_dua(
        callback.from_user.id,
        data['text'],
        category,
        arabic=data.get('arabic', '')
    )
    
    await state.clear()
    
    cat_name = DUA_CATEGORY_NAMES.get(category, category)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 {cat_name}ni ko'rish", callback_data=f"dua_page_{category}_0")],
        [InlineKeyboardButton(text="🤲 Barcha duo'lar", callback_data="view_duas")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        f"✅ Duo muvaffaqiyatli qo'shildi!\n\n"
        f"📁 Kategoriya: {cat_name}",
        reply_markup=keyboard
    )


# ==========================================
# --- Namoz Vaqtlari ---
# ==========================================

@dp.message(Command("namoz"))
async def namoz_times_handler(message: types.Message):
    """Foydalanuvchiga bugungi namoz vaqtlarini ko'rsatish"""
    user_data = get_user_full(message.from_user.id)
    city = user_data.get('city', 'Toshkent') if user_data else 'Toshkent'
    
    today = datetime.now().strftime("%Y-%m-%d")
    cached = get_cached_prayer_times(city, today)
    
    if cached:
        times = {
            "fajr": cached['fajr'],
            "dhuhr": cached['dhuhr'],
            "asr": cached['asr'],
            "maghrib": cached['maghrib'],
            "isha": cached['isha'],
        }
    else:
        times = await fetch_prayer_times(city)
        if times:
            notify_times = {k: compute_notify_time(v) for k, v in times.items()}
            save_prayer_cache(city, today, times, notify_times)
    
    text = format_prayer_times_message(times, city)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ==========================================
# --- Eslatmalar (Scheduler) qismi ---
# ==========================================

scheduler = AsyncIOScheduler()

async def refresh_prayer_cache():
    """Barcha faol shaharlar uchun namoz vaqtlarini yangilash"""
    cities = get_all_active_cities()
    today = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Namoz vaqtlarini yangilash: {len(cities)} ta shahar")
    
    for city in cities:
        cached = get_cached_prayer_times(city, today)
        if not cached:
            times = await fetch_prayer_times(city)
            if times:
                notify_times = {k: compute_notify_time(v) for k, v in times.items()}
                save_prayer_cache(city, today, times, notify_times)
                logger.info(f"✅ {city} uchun namoz vaqtlari cache'landi")
            else:
                logger.error(f"❌ {city} uchun namoz vaqtlarini olishda xatolik")
            
            await asyncio.sleep(1)  # API rate limit uchun


async def check_prayer_notifications():
    """Har daqiqada namoz eslatmalarini tekshirish"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    
    cities = get_all_active_cities()
    
    for city in cities:
        cached = get_cached_prayer_times(city, today)
        if not cached:
            continue
        
        # Har bir namoz vaqtini tekshirish
        for prayer_key in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            notify_key = f"{prayer_key}_notify"
            notify_time = cached.get(notify_key)
            
            if notify_time == current_time:
                # Bu namoz uchun eslatma vaqti keldi!
                prayer_name = PRAYER_NAMES.get(prayer_key, prayer_key)
                prayer_emoji = PRAYER_EMOJIS.get(prayer_key, "🕐")
                prayer_time = cached.get(prayer_key, "--:--")
                
                # Tegishli duo olish
                dua_category = get_prayer_dua_category(prayer_key)
                dua = get_random_dua(dua_category)
                
                # Xabar matni
                text = (
                    f"{prayer_emoji} <b>{prayer_name} namoziga oz qoldi!</b>\n"
                    f"🕐 Vaqti: <b>{prayer_time}</b>\n\n"
                    f"🤲 <i>Duo:</i>\n"
                    f"{format_dua_message(dua)}"
                )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")],
                    [InlineKeyboardButton(text="📿 Elektron Tasbeh", web_app=WebAppInfo(url=WEB_APP_URL))]
                ])
                
                # Bu shahardagi barcha foydalanuvchilarga yuborish
                users = get_users_by_city(city)
                for user_id in users:
                    try:
                        await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"Namoz eslatmasi yuborishda xatolik ({user_id}): {e}")


async def check_user_reminders():
    """Har daqiqada shaxsiy eslatmalarni tekshirish"""
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    
    try:
        resp = supabase.table('user_reminders').select('user_id').eq('time', current_time_str).eq('is_active', True).execute()
        if resp.data:
            for r in resp.data:
                user_id = r['user_id']
                text = (
                    "🔔 <b>Shaxsiy Eslatma!</b>\n\n"
                    "Siz belgilagan zikr vaqti bo'ldi. Qalbingizga taskin berish uchun zikr qilishni unutmang! 🤲"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")],
                    [InlineKeyboardButton(text="📿 Elektron Tasbeh (Web)", web_app=WebAppInfo(url=WEB_APP_URL))]
                ])
                try:
                    await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to send custom reminder to {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error checking user reminders: {e}")


async def send_morning_dua_broadcast():
    """Ertalab random tonggi duo yuborish (7:00-8:00 orasida random)"""
    response = supabase.table('users').select('user_id').execute()
    if not response.data:
        return
    
    dua = get_random_dua("morning")
    
    text = (
        "🌅 <b>Xayrli tong!</b>\n\n"
        "Kunni Allohni eslab boshlang:\n\n"
        f"{format_dua_message(dua)}\n\n"
        "<i>Bugungi zikrlaringizni ham unutmang! 📿</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")],
        [InlineKeyboardButton(text="📿 Elektron Tasbeh", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    
    for u in response.data:
        try:
            await bot.send_message(u['user_id'], text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.1)


async def send_evening_dua_broadcast():
    """Kechqurun random kechki duo yuborish"""
    response = supabase.table('users').select('user_id').execute()
    if not response.data:
        return
    
    dua = get_random_dua("evening")
    
    text = (
        "🌙 <b>Xayrli oqshom!</b>\n\n"
        "Kuningizni go'zal duo bilan yakunlang:\n\n"
        f"{format_dua_message(dua)}\n\n"
        "<i>Uxlashdan oldin zikr qilishni unutmang! 📿</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")],
        [InlineKeyboardButton(text="📿 Elektron Tasbeh", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    
    for u in response.data:
        try:
            await bot.send_message(u['user_id'], text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.1)


async def send_daily_summary():
    """Kunlik xulosa (22:30 da)"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = supabase.table('users').select('user_id').execute()
    users = [(u['user_id'],) for u in response.data]
    
    for u in users:
        user_id = u[0]
        d_resp = supabase.table('dhikrs').select('id, title, daily_target').eq('user_id', user_id).execute()
        p_resp = supabase.table('daily_progress').select('dhikr_id, count').eq('user_id', user_id).eq('date', today).execute()
        progress_dict = {p['dhikr_id']: p['count'] for p in p_resp.data}
        user_dhikrs = [(d['title'], d['daily_target'], progress_dict.get(d['id'], 0)) for d in d_resp.data]
        
        if not user_dhikrs:
            continue
            
        total_done = sum([row[2] for row in user_dhikrs])
        
        if total_done == 0:
            text = "🌙 <b>Kunlik Xulosa</b>\n\nBugun zikr qilishga vaqt topa olmadingiz shekilli. Hechqisi yo'q, ertaga albatta bajaramiz inshaalloh! 🌿\nUyqudan oldin qalbni xotirjam qilib yotishni unutmang."
        else:
            text = "🌙 <b>Kunlik Zikr Xulosasi</b>\n\nAlhamdulillah, bugungi kuningizni chiroyli amallar bilan o'tkazdingiz. Sizning bugungi natijalaringiz:\n\n"
            for title, target, current in user_dhikrs:
                if current >= target:
                    text += f"📿 <b>{title}</b>\n▫️ Qilingan: {current} ta ✅ (Maqsadga yetdingiz!)\n\n"
                elif current > 0:
                    text += f"📿 <b>{title}</b>\n▫️ Qilingan: {current} ta (Maqsad: {target} ta)\n\n"
                else:
                    text += f"📿 <b>{title}</b>\n▫️ Boshlanmadi\n\n"
            
            text += "✨ <i>Alloh taolo bugungi barcha zikrlaringizni dargohida qabul qilsin! Ertaga yangi g'ayrat bilan davom etamiz inshaalloh.</i> 🤲"
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")]])
            
        try:
            await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass


# ==========================================
# --- Action va Reminder handlers ---
# ==========================================

@dp.callback_query(F.data.startswith("start_action_"))
async def start_action_handler(callback: types.CallbackQuery):
    action = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    if action == "now":
        response = supabase.table('dhikrs').select('id, title').eq('user_id', user_id).execute()
        dhikrs = [(d['id'], d['title']) for d in response.data]
        
        if not dhikrs:
            await callback.message.edit_text("Hozircha zikrlaringiz yo'q.")
            return
            
        if len(dhikrs) == 1:
            await render_log_dhikr(callback, dhikrs[0][0], user_id)
        else:
            buttons = [[InlineKeyboardButton(text=f"📿 {d[1]}", callback_data=f"select_log_{d[0]}")] for d in dhikrs]
            buttons.append([InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="view_dhikrs")])
            await callback.message.edit_text("Qaysi zikrni o'qiymiz? Tanlang 👇", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return
        
    run_date = None
    now = datetime.now()
    text = ""
    
    if action == "1h":
        run_date = now + timedelta(hours=1)
        text = "Tushunarli, ishlaringizga baraka! 1 soatdan keyin sizga eslataman. ⏳"
    elif action == "evening":
        run_date = now.replace(hour=20, minute=0, second=0)
        if run_date <= now:
            run_date += timedelta(hours=1)
        text = "Kelishdik! Kechqurun o'zim yodga solaman. 🌙"
    elif action == "bedtime":
        run_date = now + timedelta(hours=1)
        text = "Xo'p bo'ladi, uxlashdan biroz oldin eslatib qo'yaman. 🛏"
    elif action == "morning":
        text = "Juda yaxshi, ertaga tongdan yangi g'ayrat bilan boshlaymiz! 🌅\nXayrli tun."
        
    if run_date:
        scheduler.add_job(send_specific_reminder, 'date', run_date=run_date, args=[user_id, "shaxsiy"])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Zikrlar ro'yxati", callback_data="view_dhikrs")]])
    await callback.message.edit_text(text, reply_markup=keyboard)


async def send_specific_reminder(user_id, reminder_type):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, boshlaymiz", callback_data=f"remind_yes_{reminder_type}")],
        [InlineKeyboardButton(text="⏳ Yana birozdan so'ng", callback_data=f"remind_later_{reminder_type}")]
    ])
    try:
        await bot.send_message(user_id, "Siz belgilagan vaqt bo'ldi! Zikr qilishni boshlaymizmi? 🌿", reply_markup=keyboard)
    except Exception:
        pass


@dp.callback_query(F.data.startswith("remind_yes_"))
async def remind_yes_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    response = supabase.table('dhikrs').select('id, title').eq('user_id', user_id).execute()
    dhikrs = [(d['id'], d['title']) for d in response.data]
    
    if not dhikrs:
        await callback.message.edit_text("Hozircha zikrlaringiz yo'q.")
        return
        
    if len(dhikrs) == 1:
        await render_log_dhikr(callback, dhikrs[0][0], user_id)
    else:
        buttons = [[InlineKeyboardButton(text=f"📿 {d[1]}", callback_data=f"select_log_{d[0]}")] for d in dhikrs]
        buttons.append([InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="view_dhikrs")])
        await callback.message.edit_text("Qaysi zikrni o'qiymiz? Tanlang 👇", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("remind_later_"))
async def remind_later_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    run_date = datetime.now() + timedelta(hours=1)
    scheduler.add_job(send_specific_reminder, 'date', run_date=run_date, args=[user_id, "shaxsiy"])
    await callback.message.edit_text("Tushunarli, ishlaringizga baraka! 1 soatdan keyin yana eslataman. ⏳")


# ==========================================
# --- Inline Zikr Qayd Etish (Logging) ---
# ==========================================

async def render_log_dhikr(target, dhikr_id, user_id):
    response = supabase.table('dhikrs').select('title, daily_target, global_target, global_count').eq('id', dhikr_id).eq('user_id', user_id).execute()
    if not response.data:
        return
        
    dhikr = response.data[0]
    title = dhikr['title']
    daily_tgt = dhikr['daily_target']
    global_tgt = dhikr['global_target']
    global_prog = dhikr['global_count']
    
    today = datetime.now().strftime("%Y-%m-%d")
    prog_resp = supabase.table('daily_progress').select('count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    
    if prog_resp.data:
        daily_prog = prog_resp.data[0]['count']
    else:
        daily_prog = 0
        supabase.table('daily_progress').insert({
            'user_id': user_id,
            'dhikr_id': dhikr_id,
            'date': today,
            'count': 0
        }).execute()
    
    text = (
        f"<blockquote>📿 <b>{title}</b></blockquote>\n\n"
        f"🔄 Bugungi holat: <b>{daily_prog:,} / {daily_tgt:,}</b>\n"
        f"📈 Umumiy holat: <b>{global_prog:,} / {global_tgt:,}</b>\n\n"
        f"<i>Qo'lingizda (yoki tasbehda) sanang va tayyor natijani botga kiritib boring 👇</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ 33 ta qo'shish", callback_data=f"log_add_{dhikr_id}_33"),
            InlineKeyboardButton(text="➕ 100 ta qo'shish", callback_data=f"log_add_{dhikr_id}_100")
        ],
        [InlineKeyboardButton(text="✍️ Boshqa raqam yozish", callback_data=f"log_custom_{dhikr_id}")],
        [
            InlineKeyboardButton(text="⬅️ Boshqa zikrni tanlash", callback_data="start_action_now"),
            InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")
        ]
    ])
    
    if isinstance(target, types.CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("select_log_"))
async def select_log_handler(callback: types.CallbackQuery):
    dhikr_id = int(callback.data.split("_")[2])
    await render_log_dhikr(callback, dhikr_id, callback.from_user.id)


@dp.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user = get_user(callback.from_user.id)
    if user:
        await callback.message.edit_text(
            f"Assalomu alaykum yana bir bor, hurmatli {user[0]}! 🌙\n\n"
            f"«Qalb Taskini» botiga xush kelibsiz. Zikrlarni davom ettirishingiz mumkin 👇",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.message.edit_text("Botga xush kelibsiz! Iltimos, /start buyrug'ini yuboring.")


@dp.callback_query(F.data.startswith("log_add_"))
async def log_add_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    dhikr_id = int(parts[2])
    amount = int(parts[3])
    user_id = callback.from_user.id
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    dhikr_resp = supabase.table('dhikrs').select('global_count, daily_target').eq('id', dhikr_id).execute()
    new_global = dhikr_resp.data[0]['global_count'] + amount
    daily_tgt = dhikr_resp.data[0]['daily_target']
    supabase.table('dhikrs').update({'global_count': new_global}).eq('id', dhikr_id).execute()
    
    prog_resp = supabase.table('daily_progress').select('count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    if prog_resp.data:
        new_daily = prog_resp.data[0]['count'] + amount
        supabase.table('daily_progress').update({'count': new_daily}).eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
        daily_prog = new_daily
    else:
        supabase.table('daily_progress').insert({'user_id': user_id, 'dhikr_id': dhikr_id, 'date': today, 'count': amount}).execute()
        daily_prog = amount
    
    await render_log_dhikr(callback, dhikr_id, user_id)
    
    if daily_prog >= daily_tgt and (daily_prog - amount) < daily_tgt:
        await callback.answer("🎉 Mashaa'Alloh! Bugungi maqsadingizga yetdingiz!", show_alert=True)
    else:
        await callback.answer(f"✅ +{amount} ta zikr muvaffaqiyatli qo'shildi!")

@dp.callback_query(F.data.startswith("log_custom_"))
async def log_custom_handler(callback: types.CallbackQuery, state: FSMContext):
    dhikr_id = int(callback.data.split("_")[2])
    await state.update_data(dhikr_id=dhikr_id)
    await state.set_state(LogDhikr.custom_amount)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data=f"select_log_{dhikr_id}")]
    ])
    await callback.message.edit_text("Ushbu zikrni nechta o'qiganingizni aniq raqamda yozing (masalan: 250):", reply_markup=keyboard)

@dp.message(StateFilter(LogDhikr.custom_amount))
async def process_log_custom_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat aniq raqam kiriting (masalan: 250).")
        return
        
    amount = int(message.text)
    data = await state.get_data()
    dhikr_id = data['dhikr_id']
    user_id = message.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")
    
    dhikr_resp = supabase.table('dhikrs').select('global_count').eq('id', dhikr_id).execute()
    new_global = dhikr_resp.data[0]['global_count'] + amount
    supabase.table('dhikrs').update({'global_count': new_global}).eq('id', dhikr_id).execute()
    
    prog_resp = supabase.table('daily_progress').select('count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    if prog_resp.data:
        new_daily = prog_resp.data[0]['count'] + amount
        supabase.table('daily_progress').update({'count': new_daily}).eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    else:
        supabase.table('daily_progress').insert({'user_id': user_id, 'dhikr_id': dhikr_id, 'date': today, 'count': amount}).execute()
    
    await state.clear()
    await render_log_dhikr(message, dhikr_id, user_id)
    
    await message.answer(f"✅ +{amount} ta zikr muvaffaqiyatli qo'shildi!")


# ==========================================
# --- Admin Statistika ---
# ==========================================

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    total_users_resp = supabase.table('users').select('user_id', count='exact').execute()
    total_users = total_users_resp.count
    
    today = datetime.now().strftime("%Y-%m-%d")
    active_users_resp = supabase.table('daily_progress').select('user_id', count='exact').eq('date', today).execute()
    active_users = active_users_resp.count
    
    users_resp = supabase.table('users').select('user_id, full_name, habit_level, city').execute()
    users = users_resp.data
    
    text = f"📊 <b>Admin Statistika</b>\n\n"
    text += f"👥 Umumiy foydalanuvchilar: <b>{total_users} ta</b>\n"
    text += f"🔥 Bugungi faol foydalanuvchilar: <b>{active_users} ta</b>\n\n"
    text += "📋 <b>Foydalanuvchilar ro'yxati:</b>\n"
    
    for idx, u in enumerate(users, 1):
        habit = u.get('habit_level', '')
        city = u.get('city', 'Noma\'lum')
        text += f"{idx}. {u.get('full_name', 'Ismsiz')} ({habit}) — {city}\n"
        
    if len(text) > 4000:
        text = text[:4000] + "\n...va boshqalar."
        
    await message.answer(text, parse_mode="HTML")


# ==========================================
# --- Sozlamalar (Settings) ---
# ==========================================

@dp.callback_query(F.data == "settings")
async def settings_handler(callback: types.CallbackQuery):
    response = supabase.table('users').select('full_name, age, habit_level, city, prayer_notifications').eq('user_id', callback.from_user.id).execute()
    if response.data:
        ud = response.data[0]
    else:
        await callback.message.edit_text("Foydalanuvchi topilmadi. /start ni bosing.")
        return
    
    name = ud.get('full_name', 'Noma\'lum')
    age = ud.get('age', '')
    habit = ud.get('habit_level', '')
    city = ud.get('city', 'Toshkent')
    prayer_on = ud.get('prayer_notifications', True)
    
    habit_text = {
        "beginner": "🌱 Yangi boshlayapman",
        "medium": "🌿 Vaqt topganda qilaman",
        "advanced": "🌳 Doimiy odatim bor"
    }.get(habit, habit)
    
    age_text = {
        "under20": "20 yoshgacha",
        "21-30": "21-30 yosh",
        "31-50": "31-50 yosh",
        "over50": "50 yoshdan yuqori"
    }.get(age, f"{age} yosh")
    
    prayer_status = "✅ Yoqilgan" if prayer_on else "❌ O'chirilgan"
    
    text = (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"⏳ Yosh: <b>{age_text}</b>\n"
        f"🔄 Odat: <b>{habit_text}</b>\n"
        f"🌍 Shahar: <b>{city}</b>\n"
        f"🕌 Namoz eslatmalari: <b>{prayer_status}</b>\n\n"
        "<i>Quyidagilardan birini tanlang:</i>"
    )
    
    prayer_btn_text = "🕌 Namoz eslatmalarini O'CHIRISH" if prayer_on else "🕌 Namoz eslatmalarini YOQISH"
    prayer_action = "settings_prayer_off" if prayer_on else "settings_prayer_on"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Ismni o'zgartirish", callback_data="settings_name")],
        [InlineKeyboardButton(text="🌍 Shaharni o'zgartirish", callback_data="settings_city")],
        [InlineKeyboardButton(text=prayer_btn_text, callback_data=prayer_action)],
        [InlineKeyboardButton(text="📊 Zikr odatini o'zgartirish", callback_data="settings_habit")],
        [InlineKeyboardButton(text="🕌 Namoz vaqtlari", callback_data="settings_prayer_times")],
        [InlineKeyboardButton(text="🗑 Barcha ma'lumotlarni o'chirish", callback_data="settings_reset")],
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "settings_name")
async def settings_name_handler(callback: types.CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="settings")]])
    await callback.message.edit_text("Yangi ismingizni kiriting:", reply_markup=keyboard)
    await state.set_state(SettingsState.change_name)

@dp.message(StateFilter(SettingsState.change_name))
async def process_settings_name(message: types.Message, state: FSMContext):
    new_name = message.text
    supabase.table('users').update({'full_name': new_name}).eq('user_id', message.from_user.id).execute()
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚙️ Sozlamalarga qaytish", callback_data="settings")]])
    await message.answer(f"Ismingiz <b>{new_name}</b> ga o'zgartirildi ✅", reply_markup=keyboard, parse_mode="HTML")

# --- Shahar o'zgartirish ---

@dp.callback_query(F.data == "settings_city")
async def settings_city_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🌍 Yangi shahringizni tanlang:",
        reply_markup=get_city_keyboard()
    )

@dp.callback_query(F.data.startswith("city_"), ~StateFilter(Onboarding.city))
async def settings_city_select_handler(callback: types.CallbackQuery):
    city = callback.data[5:]
    supabase.table('users').update({'city': city}).eq('user_id', callback.from_user.id).execute()
    
    # Yangi shahar uchun namoz vaqtlarini cache'lash
    today = datetime.now().strftime("%Y-%m-%d")
    cached = get_cached_prayer_times(city, today)
    if not cached:
        times = await fetch_prayer_times(city)
        if times:
            notify_times = {k: compute_notify_time(v) for k, v in times.items()}
            save_prayer_cache(city, today, times, notify_times)
    
    await callback.answer(f"✅ Shahringiz {city} ga o'zgartirildi!")
    await settings_handler(callback)

# --- Namoz eslatmalari toggle ---

@dp.callback_query(F.data == "settings_prayer_on")
async def settings_prayer_on_handler(callback: types.CallbackQuery):
    supabase.table('users').update({'prayer_notifications': True}).eq('user_id', callback.from_user.id).execute()
    await callback.answer("✅ Namoz eslatmalari yoqildi!")
    await settings_handler(callback)

@dp.callback_query(F.data == "settings_prayer_off")
async def settings_prayer_off_handler(callback: types.CallbackQuery):
    supabase.table('users').update({'prayer_notifications': False}).eq('user_id', callback.from_user.id).execute()
    await callback.answer("❌ Namoz eslatmalari o'chirildi!")
    await settings_handler(callback)

# --- Namoz vaqtlarini ko'rish ---

@dp.callback_query(F.data == "settings_prayer_times")
async def settings_prayer_times_handler(callback: types.CallbackQuery):
    user_data = get_user_full(callback.from_user.id)
    city = user_data.get('city', 'Toshkent') if user_data else 'Toshkent'
    
    today = datetime.now().strftime("%Y-%m-%d")
    cached = get_cached_prayer_times(city, today)
    
    if cached:
        times = {k: cached[k] for k in ["fajr", "dhuhr", "asr", "maghrib", "isha"]}
    else:
        times = await fetch_prayer_times(city)
        if times:
            notify_times = {k: compute_notify_time(v) for k, v in times.items()}
            save_prayer_cache(city, today, times, notify_times)
    
    text = format_prayer_times_message(times, city)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Sozlamalarga qaytish", callback_data="settings")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# --- Zikr odati ---

@dp.callback_query(F.data == "settings_habit")
async def settings_habit_handler(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Yangi boshlayapman", callback_data="set_habit_beginner")],
        [InlineKeyboardButton(text="🌿 Vaqt topganda qilaman", callback_data="set_habit_medium")],
        [InlineKeyboardButton(text="🌳 Doimiy odatim bor", callback_data="set_habit_advanced")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="settings")]
    ])
    await callback.message.edit_text("Kunlik zikr qilish odatingizni yangilang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("set_habit_"))
async def process_settings_habit(callback: types.CallbackQuery):
    new_habit = callback.data.split("_")[2]
    supabase.table('users').update({'habit_level': new_habit}).eq('user_id', callback.from_user.id).execute()
    
    await callback.answer("Zikr odatingiz yangilandi ✅")
    await settings_handler(callback)

# --- Ma'lumotlarni o'chirish ---

@dp.callback_query(F.data == "settings_reset")
async def settings_reset_handler(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ HA, HAMMASINI O'CHIRISH", callback_data="settings_reset_confirm")],
        [InlineKeyboardButton(text="⬅️ Yo'q, qaytish", callback_data="settings")]
    ])
    await callback.message.edit_text("⚠️ <b>DIQQAT!</b>\n\nSizning barcha saqlangan zikrlaringiz, duolar, kunlik statistika va umuman hamma natijalaringiz qaytarib bo'lmaydigan qilib o'chiriladi. Ishonchingiz komilmi?", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "settings_reset_confirm")
async def settings_reset_confirm_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    supabase.table('daily_progress').delete().eq('user_id', user_id).execute()
    supabase.table('dhikrs').delete().eq('user_id', user_id).execute()
    supabase.table('duas').delete().eq('user_id', user_id).execute()
    supabase.table('user_reminders').delete().eq('user_id', user_id).execute()
    supabase.table('users').delete().eq('user_id', user_id).execute()
    
    await state.clear()
    await callback.message.edit_text("🗑 Barcha ma'lumotlaringiz o'chirildi.\n\nYangi hayot boshlash uchun /start buyrug'ini yuboring.")


# ==========================================
# --- Main ---
# ==========================================

async def main() -> None:
    init_db()
    
    # Bot komandalarini o'rnatish
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="namoz", description="Bugungi namoz vaqtlari"),
        BotCommand(command="stats", description="Admin statistika (faqat adminlar uchun)")
    ])
    
    # --- Scheduler job'lari ---
    
    # 1. Namoz vaqtlarini har kuni yangilash (00:05 da)
    scheduler.add_job(refresh_prayer_cache, 'cron', hour=0, minute=5, id='refresh_prayer')
    
    # 2. Bot start bo'lganda ham darhol cache'lash
    scheduler.add_job(refresh_prayer_cache, 'date', run_date=datetime.now() + timedelta(seconds=5), id='refresh_prayer_startup')
    
    # 3. Har daqiqada namoz eslatmalarini tekshirish
    scheduler.add_job(check_prayer_notifications, 'cron', minute='*', id='prayer_notifications')
    
    # 4. Har daqiqada shaxsiy eslatmalarni tekshirish
    scheduler.add_job(check_user_reminders, 'cron', minute='*', id='user_reminders')
    
    # 5. Tonggi duo (random vaqtda 6:30-7:30 orasida)
    morning_minute = random.randint(0, 59)
    scheduler.add_job(send_morning_dua_broadcast, 'cron', hour=6, minute=morning_minute, id='morning_dua')
    
    # 6. Kechki duo (random vaqtda 20:00-20:59 orasida)
    evening_minute = random.randint(0, 59)
    scheduler.add_job(send_evening_dua_broadcast, 'cron', hour=20, minute=evening_minute, id='evening_dua')
    
    # 7. Kunlik xulosa (22:30 da)
    scheduler.add_job(send_daily_summary, 'cron', hour=22, minute=30, id='daily_summary')
    
    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi")
    logger.info(f"  📿 Tonggi duo: 06:{morning_minute:02d}")
    logger.info(f"  📿 Kechki duo: 20:{evening_minute:02d}")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
