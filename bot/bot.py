import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import math
import random
from dotenv import load_dotenv
from database import init_db, save_user_data, add_default_dhikr, get_user, DB_PATH

# Muhit o'zgaruvchilarini yuklash
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Loggingni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Vaqtincha Web App URL
WEB_APP_URL = "https://your-vercel-app-url.vercel.app/"

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
    await state.update_data(full_name=callback.from_user.first_name)
    await ask_for_age(callback.message, state)

@dp.message(StateFilter(Onboarding.name))
async def process_name_text(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await ask_for_age(message, state)

@dp.callback_query(StateFilter(Onboarding.age), F.data.startswith("age_"))
async def process_age(callback: types.CallbackQuery, state: FSMContext):
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT dhikr_id, title, daily_target, global_target, global_progress FROM Dhikrs WHERE user_id=?", (callback.from_user.id,))
    dhikrs = cursor.fetchall()
    conn.close()
    
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
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Dhikrs (user_id, title, daily_target, global_target) VALUES (?, ?, ?, ?)", (callback.from_user.id, title, daily_tgt, global_tgt))
        conn.commit()
        conn.close()
                
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
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Dhikrs (user_id, title, daily_target, global_target) VALUES (?, ?, ?, ?)", (message.from_user.id, title, daily_tgt, global_tgt))
    conn.commit()
    conn.close()
            
    await state.clear()
    
    await state.clear()
    
    keyboard = get_start_action_keyboard()
    await message.answer(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")


# --- 2. Zikrni Tahrirlash FSM ---

@dp.callback_query(F.data.startswith("edit_dhikr_"))
async def edit_dhikr_handler(callback: types.CallbackQuery, state: FSMContext):
    dhikr_id = int(callback.data.split("_")[2])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM Dhikrs WHERE dhikr_id=?", (dhikr_id,))
    title = cursor.fetchone()[0]
    conn.close()
    
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
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE Dhikrs SET daily_target=?, global_target=? WHERE dhikr_id=?", (daily_tgt, global_tgt, dhikr_id))
        conn.commit()
        conn.close()
                
        await state.clear()
        keyboard = get_start_action_keyboard()
        
        # We need the title to show the completion message.
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM Dhikrs WHERE dhikr_id=?", (dhikr_id,))
        title = cursor.fetchone()[0]
        conn.close()
        
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
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE Dhikrs SET daily_target=?, global_target=? WHERE dhikr_id=?", (daily_tgt, global_tgt, dhikr_id))
    cursor.execute("SELECT title FROM Dhikrs WHERE dhikr_id=?", (dhikr_id,))
    title = cursor.fetchone()[0]
    conn.commit()
    conn.close()
            
    await state.clear()
    
    await state.clear()
    
    keyboard = get_start_action_keyboard()
    await message.answer(get_completion_msg(title, daily_tgt, global_tgt), reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "settings")
async def settings_handler(callback: types.CallbackQuery):
    await callback.answer("Sozlamalar bo'limi tez orada ishga tushadi!", show_alert=True)

# ==========================================
# --- Eslatmalar (Scheduler) qismi ---
# ==========================================

scheduler = AsyncIOScheduler()

async def broadcast_reminder(reminder_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users")
    users = cursor.fetchall()
    conn.close()
    
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

@dp.callback_query(F.data.startswith("start_action_"))
async def start_action_handler(callback: types.CallbackQuery):
    action = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    if action == "now":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT dhikr_id, title FROM Dhikrs WHERE user_id=?", (user_id,))
        dhikrs = cursor.fetchall()
        conn.close()
        
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT dhikr_id, title FROM Dhikrs WHERE user_id=?", (user_id,))
    dhikrs = cursor.fetchall()
    conn.close()
    
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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, daily_target, global_target, global_progress FROM Dhikrs WHERE dhikr_id=? AND user_id=?", (dhikr_id, user_id))
    dhikr = cursor.fetchone()
    if not dhikr:
        conn.close()
        return
        
    title, daily_tgt, global_tgt, global_prog = dhikr
    
    # Bugungi sanani olish va jadvalga qo'shish/tekshirish
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT current_count FROM Daily_Progress WHERE user_id=? AND dhikr_id=? AND date=?", (user_id, dhikr_id, today))
    daily_prog_row = cursor.fetchone()
    if daily_prog_row:
        daily_prog = daily_prog_row[0]
    else:
        daily_prog = 0
        cursor.execute("INSERT INTO Daily_Progress (user_id, dhikr_id, date, current_count) VALUES (?, ?, ?, ?)", (user_id, dhikr_id, today, 0))
        conn.commit()
        
    conn.close()
    
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
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE Dhikrs SET global_progress = global_progress + ? WHERE dhikr_id=?", (amount, dhikr_id))
    cursor.execute("""
        INSERT INTO Daily_Progress (user_id, dhikr_id, date, current_count) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, dhikr_id, date) DO UPDATE SET current_count = current_count + ?
    """, (user_id, dhikr_id, today, amount, amount))
    conn.commit()
    
    cursor.execute("SELECT daily_target FROM Dhikrs WHERE dhikr_id=?", (dhikr_id,))
    daily_tgt = cursor.fetchone()[0]
    cursor.execute("SELECT current_count FROM Daily_Progress WHERE user_id=? AND dhikr_id=? AND date=?", (user_id, dhikr_id, today))
    daily_prog = cursor.fetchone()[0]
    conn.close()
    
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
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE Dhikrs SET global_progress = global_progress + ? WHERE dhikr_id=?", (amount, dhikr_id))
    cursor.execute("""
        INSERT INTO Daily_Progress (user_id, dhikr_id, date, current_count) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, dhikr_id, date) DO UPDATE SET current_count = current_count + ?
    """, (user_id, dhikr_id, today, amount, amount))
    conn.commit()
    conn.close()
    
    await state.clear()
    await render_log_dhikr(message, dhikr_id, user_id)
    
    # Option to celebrate here too, but doing it simply:
    await message.answer(f"✅ +{amount} ta zikr muvaffaqiyatli qo'shildi!")

async def main() -> None:
    init_db()
    
    # Eslatmalarni jadvalga qo'shish (Vaqtlarni O'zbekiston vaqtiga moslab olish kerak)
    scheduler.add_job(broadcast_reminder, 'cron', hour=8, minute=0, args=["morning"])
    scheduler.add_job(broadcast_reminder, 'cron', hour=13, minute=0, args=["day"])
    scheduler.add_job(broadcast_reminder, 'cron', hour=17, minute=0, args=["afternoon"])
    scheduler.add_job(broadcast_reminder, 'cron', hour=21, minute=0, args=["evening"])
    scheduler.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
