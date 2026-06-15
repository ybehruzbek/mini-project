import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.types.web_app_info import WebAppInfo
from datetime import datetime, timedelta
import math
import random
from dotenv import load_dotenv
from database import init_db, save_user_data, add_default_dhikr, get_user, supabase

ADMIN_ID = 1277687464

# Muhit o'zgaruvchilarini yuklash
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Vaqtincha Web App URL
WEB_APP_URL = "https://ybehruzbek.github.io/mini-project/"

# Anketa holatlari (States)
class Onboarding(StatesGroup):
    name = State()
    age = State()
    gender = State()
    habit = State()

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

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Zikrni Boshlash", callback_data="start_action_now")],
        [InlineKeyboardButton(text="📿 Elektron Tasbeh (Web)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🤲 Zikrlarni ko'rish", callback_data="view_dhikrs")],
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


@dp.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    # Eski foydalanuvchi ekanligini tekshiramiz
    user = get_user(message.from_user.id)
    if user:
        name = user[0]
        await message.answer(
            f"Assalomu alaykum yana bir bor, hurmatli {name}! 🌙\n\n"
            "«Qalb Taskini» botiga xush kelibsiz. Zikrlarni davom ettirishingiz mumkin 👇",
            reply_markup=get_main_keyboard()
        )
        return

    # Yangi foydalanuvchi bo'lsa, anketa boshlanadi
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

# Yosh so'rash uchun umumiy funksiya (kodni qayta ishlatish uchun)
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
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    save_user_data(user_id, data)
    add_default_dhikr(user_id, habit)
    
    await state.clear()
    
    name = data.get('full_name', "Do'stim")
    
    await callback.message.answer(
        f"Rahmat, hurmatli {name}! Ma'lumotlaringiz muvaffaqiyatli saqlandi. ✅\n\n"
        "Odatingizga mos ravishda kunlik zikrlarni belgilab qo'ydim.\n\n"
        "Quyidagi tugma orqali elektron tasbehni ochishingiz mumkin 👇",
        reply_markup=get_main_keyboard()
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

@dp.callback_query(F.data == "view_dhikrs")
async def view_dhikrs_handler(callback: types.CallbackQuery):
    response = supabase.table('dhikrs').select('id, title, daily_target, global_target, global_progress').eq('user_id', callback.from_user.id).execute()
    dhikrs = [(d['id'], d['title'], d['daily_target'], d['global_target'], d['global_progress']) for d in response.data]
    
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
        # state remains daily_target
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
        # state remains global_target
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
            'global_progress': 0
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
            'global_progress': 0
        }).execute()
            
    await state.clear()
    
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
        
        # We need the title to show the completion message.
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
    pass
            
    await state.clear()
    
    await state.clear()
    
    keyboard = get_start_action_keyboard()
    await message.answer(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")


# ==========================================
# --- Eslatmalar (Scheduler) qismi ---
# ==========================================

scheduler = AsyncIOScheduler()

async def broadcast_reminder(reminder_type):
    response = supabase.table('users').select('user_id').execute()
    users = [(u['user_id'],) for u in response.data]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, boshlaymiz", callback_data=f"remind_yes_{reminder_type}")],
        [InlineKeyboardButton(text="⏳ Birozdan so'ng", callback_data=f"remind_later_{reminder_type}")]
    ])
    
    msg_text = "Hozir ruhiyatni tinchlantirish uchun 2-3 daqiqa vaqtingiz bormi? 🌿"
    
    morning_msgs = [
        "Xayrli tong! Kunning barakasi zikrdadir. Boshlaymizmi? 🌅",
        "Yangi kun, yangi umidlar! Bugungi kuningizni zikr bilan yoriting! ✨",
        "Assalomu alaykum! Tonggi zikrlarni aytishga vaqt ajratamizmi? 🕊"
    ]
    day_msgs = [
        "Tushlik vaqti bo'ldi. Ruhiyatni ham ozgina oziqlantiramizmi? 🍃",
        "Ishlardan biroz chalg'ib, zikrga 2 daqiqa ajratamiz! ⏳",
        "Kuningiz qanday o'tyapti? Zikr aytib, biroz xotirjamlik toping. 🌸"
    ]
    evening_msgs = [
        "Kuningiz xayrli o'tdimi? Uxlashdan oldin qalbni xotirjam qilaylik. 🌙",
        "Bugungi kun amallarini go'zal zikrlar bilan yakunlaymiz! 🌟",
        "Kech tushdi, endi o'zimizga biroz vaqt ajratamizmi? 📿"
    ]
    
    if reminder_type == "morning":
        msg_text = random.choice(morning_msgs)
    elif reminder_type in ["day", "afternoon"]:
        msg_text = random.choice(day_msgs)
    elif reminder_type == "evening":
        msg_text = random.choice(evening_msgs)
        
    for u in users:
        try:
            await bot.send_message(u[0], msg_text, reply_markup=keyboard)
        except Exception:
            pass

async def send_specific_reminder(user_id, reminder_type):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, boshlaymiz", callback_data=f"remind_yes_{reminder_type}")],
        [InlineKeyboardButton(text="⏳ Yana birozdan so'ng", callback_data=f"remind_later_{reminder_type}")]
    ])
    try:
        await bot.send_message(user_id, "Siz belgilagan vaqt bo'ldi! Zikr qilishni boshlaymizmi? 🌿", reply_markup=keyboard)
    except Exception:
        pass

async def send_daily_summary():
    today = datetime.now().strftime("%Y-%m-%d")
    response = supabase.table('users').select('user_id').execute()
    users = [(u['user_id'],) for u in response.data]
    
    for u in users:
        user_id = u[0]
        cursor.execute("SELECT d.title, d.daily_target, IFNULL(dp.current_count, 0) FROM Dhikrs d LEFT JOIN Daily_Progress dp ON d.dhikr_id = dp.dhikr_id AND dp.date = ? WHERE d.user_id = ?", (today, user_id))
        user_dhikrs = cursor.fetchall()
        
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
            
    pass

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
    response = supabase.table('dhikrs').select('title, daily_target, global_target, global_progress').eq('id', dhikr_id).eq('user_id', user_id).execute()
    if not response.data:
        return
        
    dhikr = response.data[0]
    title = dhikr['title']
    daily_tgt = dhikr['daily_target']
    global_tgt = dhikr['global_target']
    global_prog = dhikr['global_progress']
    
    # Bugungi sanani olish va jadvalga qo'shish/tekshirish
    today = datetime.now().strftime("%Y-%m-%d")
    prog_resp = supabase.table('daily_progress').select('current_count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    
    if prog_resp.data:
        daily_prog = prog_resp.data[0]['current_count']
    else:
        daily_prog = 0
        supabase.table('daily_progress').insert({
            'user_id': user_id,
            'dhikr_id': dhikr_id,
            'date': today,
            'current_count': 0
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

@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    # Umumiy foydalanuvchilar
    total_users_resp = supabase.table('users').select('user_id', count='exact').execute()
    total_users = total_users_resp.count
    
    # Bugun faol bo'lganlar (bugun zikr qilganlar)
    today = datetime.now().strftime("%Y-%m-%d")
    active_users_resp = supabase.table('daily_progress').select('user_id', count='exact').eq('date', today).execute()
    active_users = active_users_resp.count
    
    # Foydalanuvchilar ro'yxati
    users_resp = supabase.table('users').select('user_id, full_name, habit_level').execute()
    users = users_resp.data
    
    text = f"📊 <b>Admin Statistika</b>\n\n"
    text += f"👥 Umumiy foydalanuvchilar: <b>{total_users} ta</b>\n"
    text += f"🔥 Bugungi faol foydalanuvchilar: <b>{active_users} ta</b>\n\n"
    text += "📋 <b>Foydalanuvchilar ro'yxati:</b>\n"
    
    for idx, u in enumerate(users, 1):
        habit = u.get('habit_level', '')
        text += f"{idx}. {u.get('full_name', 'Ismsiz')} ({habit})\n"
        
    if len(text) > 4000:
        text = text[:4000] + "\n...va boshqalar."
        
    await message.answer(text, parse_mode="HTML")

# ==========================================
# --- Sozlamalar (Settings) ---
# ==========================================

@dp.callback_query(F.data == "settings")
async def settings_handler(callback: types.CallbackQuery):
    response = supabase.table('users').select('full_name, age, habit_level').eq('user_id', callback.from_user.id).execute()
    if response.data:
        ud = response.data[0]
        user_data = (ud['full_name'], ud['age'], ud['habit_level'])
    else:
        user_data = None
    
    if not user_data:
        await callback.message.edit_text("Foydalanuvchi topilmadi. /start ni bosing.")
        return
        
    name, age, habit = user_data
    
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
    
    text = (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"👤 Ism: <b>{name}</b>\n"
        f"⏳ Yosh: <b>{age_text}</b>\n"
        f"🔄 Odat: <b>{habit_text}</b>\n\n"
        "<i>Quyidagilardan birini tanlang:</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Ismni o'zgartirish", callback_data="settings_name")],
        [InlineKeyboardButton(text="📊 Zikr odatini o'zgartirish", callback_data="settings_habit")],
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

@dp.callback_query(F.data == "settings_reset")
async def settings_reset_handler(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ HA, HAMMASINI O'CHIRISH", callback_data="settings_reset_confirm")],
        [InlineKeyboardButton(text="⬅️ Yo'q, qaytish", callback_data="settings")]
    ])
    await callback.message.edit_text("⚠️ <b>DIQQAT!</b>\n\nSizning barcha saqlangan zikrlaringiz, kunlik statistika va umuman hamma natijalaringiz qaytarib bo'lmaydigan qilib o'chiriladi. Ishonchingiz komilmi?", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "settings_reset_confirm")
async def settings_reset_confirm_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    supabase.table('daily_progress').delete().eq('user_id', user_id).execute()
    supabase.table('dhikrs').delete().eq('user_id', user_id).execute()
    supabase.table('users').delete().eq('user_id', user_id).execute()
    pass
    
    await state.clear()
    await callback.message.edit_text("🗑 Barcha ma'lumotlaringiz o'chirildi.\n\nYangi hayot boshlash uchun /start buyrug'ini yuboring.")

@dp.callback_query(F.data.startswith("log_add_"))
async def log_add_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    dhikr_id = int(parts[2])
    amount = int(parts[3])
    user_id = callback.from_user.id
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    dhikr_resp = supabase.table('dhikrs').select('global_progress, daily_target').eq('id', dhikr_id).execute()
    new_global = dhikr_resp.data[0]['global_progress'] + amount
    daily_tgt = dhikr_resp.data[0]['daily_target']
    supabase.table('dhikrs').update({'global_progress': new_global}).eq('id', dhikr_id).execute()
    
    prog_resp = supabase.table('daily_progress').select('current_count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    if prog_resp.data:
        new_daily = prog_resp.data[0]['current_count'] + amount
        supabase.table('daily_progress').update({'current_count': new_daily}).eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
        daily_prog = new_daily
    else:
        supabase.table('daily_progress').insert({'user_id': user_id, 'dhikr_id': dhikr_id, 'date': today, 'current_count': amount}).execute()
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
    
    dhikr_resp = supabase.table('dhikrs').select('global_progress').eq('id', dhikr_id).execute()
    new_global = dhikr_resp.data[0]['global_progress'] + amount
    supabase.table('dhikrs').update({'global_progress': new_global}).eq('id', dhikr_id).execute()
    
    prog_resp = supabase.table('daily_progress').select('current_count').eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    if prog_resp.data:
        new_daily = prog_resp.data[0]['current_count'] + amount
        supabase.table('daily_progress').update({'current_count': new_daily}).eq('user_id', user_id).eq('dhikr_id', dhikr_id).eq('date', today).execute()
    else:
        supabase.table('daily_progress').insert({'user_id': user_id, 'dhikr_id': dhikr_id, 'date': today, 'current_count': amount}).execute()
    
    await state.clear()
    await render_log_dhikr(message, dhikr_id, user_id)
    
    # Option to celebrate here too, but doing it simply:
    await message.answer(f"✅ +{amount} ta zikr muvaffaqiyatli qo'shildi!")

async def main() -> None:
    init_db()
    
    # Bot komandalarini o'rnatish
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni qayta ishga tushirish"),
        BotCommand(command="stats", description="Admin statistika (faqat adminlar uchun)")
    ])
    
    # Umumiy eslatmalar
    scheduler.add_job(broadcast_reminder, 'cron', hour=8, minute=0, args=["morning"])
    scheduler.add_job(broadcast_reminder, 'cron', hour=13, minute=0, args=["day"])
    scheduler.add_job(broadcast_reminder, 'cron', hour=17, minute=0, args=["afternoon"])
    scheduler.add_job(broadcast_reminder, 'cron', hour=21, minute=0, args=["evening"])
    
    # Kunlik xulosa (22:30 da)
    scheduler.add_job(send_daily_summary, 'cron', hour=22, minute=30)
    
    scheduler.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
