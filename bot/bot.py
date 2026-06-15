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

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📿 Tasbehni ochish", web_app=WebAppInfo(url=WEB_APP_URL))],
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Zikrlar ro'yxati", callback_data="view_dhikrs")]])
        await callback.message.edit_text(f"✅ Yangi zikr muvaffaqiyatli qo'shildi:\n\n📿 {title}\nKunlik: {daily_tgt} ta | Umumiy: {global_tgt} ta", reply_markup=keyboard)


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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Zikrlar ro'yxati", callback_data="view_dhikrs")]
    ])
    await message.answer(f"✅ Yangi zikr muvaffaqiyatli qo'shildi:\n\n📿 {title}\nKunlik: {daily_tgt} ta | Umumiy: {global_tgt} ta", reply_markup=keyboard)


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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Zikrlar ro'yxati", callback_data="view_dhikrs")]])
        await callback.message.edit_text("✅ Zikr maqsadi muvaffaqiyatli yangilandi!", reply_markup=keyboard)


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
    conn.commit()
    conn.close()
            
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Zikrlar ro'yxati", callback_data="view_dhikrs")]
    ])
    await message.answer("✅ Zikr maqsadi muvaffaqiyatli yangilandi!", reply_markup=keyboard)

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
    if reminder_type == "morning":
        msg_text = "Xayrli tong! Bugungi zikr rejamizni boshlashga tayyormisiz? 🌅"
    elif reminder_type == "evening":
        msg_text = "Kuningiz xayrli o'tdimi? Uxlashdan oldin zikrlarni to'ldirib qo'yamizmi? 🌙"
        
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
        await bot.send_message(user_id, "Vaqtingiz bo'ldimi? Zikr qilishni boshlaymizmi? 🌿", reply_markup=keyboard)
    except Exception:
        pass

@dp.callback_query(F.data.startswith("remind_yes_"))
async def remind_yes_handler(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📿 Tasbehni ochish", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await callback.message.edit_text("Barakalloh! Tasbehni ochib, zikrlarni boshlashingiz mumkin 👇", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("remind_later_"))
async def remind_later_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    reminder_type = callback.data.split("_")[2]
    
    run_date = datetime.now() + timedelta(hours=1)
    scheduler.add_job(send_specific_reminder, 'date', run_date=run_date, args=[user_id, reminder_type])
    
    await callback.message.edit_text("Tushunarli, ishlaringizga baraka! 1 soatdan keyin yana eslataman. ⏳")

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
