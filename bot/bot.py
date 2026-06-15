import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv
from database import init_db, save_user_data, add_default_dhikr

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

@dp.message(CommandStart())
async def command_start_handler(message: types.Message, state: FSMContext) -> None:
    first_name = message.from_user.first_name
    
    welcome_msg = await message.answer(
        f"Assalomu alaykum, {first_name}! 🌙\n\n"
        "«Qalb Taskini» — ruhiy xotirjamlik va doimiy zikrda bo'lishingiz uchun yaratilgan shaxsiy yordamchingiz.\n\n"
        "Bu yerda siz o'z zikrlaringizni tartibga solishingiz, eslatmalar olishingiz va qulay elektron tasbehdan foydalanishingiz mumkin. 🌿"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Ha, '{first_name}' qolaversin", callback_data="use_tg_name")]
    ])
    
    question_msg = await message.answer(
        f"Siz bilan yaqinroq tanishishim va botni aynan sizga moslashim uchun ismingiz kerak.\n\n"
        f"Sizga Telegramdagi ismingiz ({first_name}) bilan murojaat qilaymi yoki bu yerga o'zingiz boshqa ism yozasizmi?",
        reply_markup=keyboard
    )
    
    # Xabarlarni tozalash uchun ro'yxatni boshlaymiz
    await state.update_data(messages_to_delete=[message.message_id, welcome_msg.message_id, question_msg.message_id])
    await state.set_state(Onboarding.name)

# Yosh so'rash uchun umumiy funksiya (kodni qayta ishlatish uchun)
async def ask_for_age(target_message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 20 yoshgacha", callback_data="age_under20")],
        [InlineKeyboardButton(text="🌿 21-30 yosh", callback_data="age_21-30")],
        [InlineKeyboardButton(text="🌳 31-50 yosh", callback_data="age_31-50")],
        [InlineKeyboardButton(text="🏔 50 yoshdan yuqori", callback_data="age_over50")]
    ])
    msg = await target_message.answer("Sizga moslashtirishim uchun, yosh oralig'ingizni belgilang:", reply_markup=keyboard)
    
    data = await state.get_data()
    messages = data.get('messages_to_delete', [])
    messages.append(msg.message_id)
    await state.update_data(messages_to_delete=messages)
    await state.set_state(Onboarding.age)

@dp.callback_query(StateFilter(Onboarding.name), F.data == "use_tg_name")
async def process_name_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(full_name=callback.from_user.first_name)
    await callback.message.delete()
    await ask_for_age(callback.message, state)

@dp.message(StateFilter(Onboarding.name))
async def process_name_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    messages = data.get('messages_to_delete', [])
    messages.append(message.message_id)
    await state.update_data(messages_to_delete=messages)
    
    await state.update_data(full_name=message.text)
    await ask_for_age(message, state)

@dp.callback_query(StateFilter(Onboarding.age), F.data.startswith("age_"))
async def process_age(callback: types.CallbackQuery, state: FSMContext):
    age_group = callback.data.split("_")[1]
    await state.update_data(age=age_group)
    
    # Oldingi yosh tugmalarini o'chiramiz
    await callback.message.delete()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Erkak", callback_data="gender_male"),
         InlineKeyboardButton(text="👩 Ayol", callback_data="gender_female")]
    ])
    msg = await callback.message.answer("Jinsingizni belgilang:", reply_markup=keyboard)
    
    data = await state.get_data()
    messages = data.get('messages_to_delete', [])
    messages.append(msg.message_id)
    await state.update_data(messages_to_delete=messages)
    await state.set_state(Onboarding.gender)

@dp.callback_query(StateFilter(Onboarding.gender), F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    
    await callback.message.delete()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌱 Yangi boshlayapman", callback_data="habit_beginner")],
        [InlineKeyboardButton(text="🌿 Vaqt topganda qilaman", callback_data="habit_medium")],
        [InlineKeyboardButton(text="🌳 Doimiy odatim bor", callback_data="habit_advanced")]
    ])
    msg = await callback.message.answer("Kunlik zikr qilish odatingiz qanday?", reply_markup=keyboard)
    
    data = await state.get_data()
    messages = data.get('messages_to_delete', [])
    messages.append(msg.message_id)
    await state.update_data(messages_to_delete=messages)
    
    await state.set_state(Onboarding.habit)

@dp.callback_query(StateFilter(Onboarding.habit), F.data.startswith("habit_"))
async def process_habit(callback: types.CallbackQuery, state: FSMContext):
    habit = callback.data.split("_")[1]
    await state.update_data(habit_level=habit)
    
    data = await state.get_data()
    user_id = callback.from_user.id
    
    save_user_data(user_id, data)
    add_default_dhikr(user_id, habit)
    
    await callback.message.delete()
    
    messages_to_delete = data.get('messages_to_delete', [])
    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass
    
    await state.clear()
    
    name = data['full_name']
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📿 Tasbehni ochish", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="🤲 Zikrlarni ko'rish", callback_data="view_dhikrs")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings")]
    ])
    
    await callback.message.answer(
        f"Rahmat, hurmatli {name}! Ma'lumotlaringiz muvaffaqiyatli saqlandi. ✅\n\n"
        "Odatingizga mos ravishda kunlik zikrlarni belgilab qo'ydim.\n\n"
        "Quyidagi tugma orqali elektron tasbehni ochishingiz mumkin 👇",
        reply_markup=keyboard
    )

async def main() -> None:
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
