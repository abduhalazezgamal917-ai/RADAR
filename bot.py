import os
import json
import asyncio
import logging
from flask import Flask
from threading import Thread

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from aiogram.filters import Command

# ========= Logging =========
logging.basicConfig(level=logging.INFO)

# ========= Config =========
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEV_ID = int(os.getenv("DEV_ID", 6043858925))
BOT_USERNAME = "RA_G_bot"
BOT_NAME = "RADAR"

bot = Bot(token=BOT_TOKEN, parse_mode="Markdown")
dp = Dispatcher()

# ========= Database =========
DATA_FILE = "users.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": [], "settings": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(db, f)

db = load_data()

def add_user(user_id):
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_data()

# ========= Keep Alive =========
app = Flask('')

@app.route('/')
def home():
    return "Bot Alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ========= Utils =========
async def is_admin(chat_id, user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

# ========= UI =========
def main_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ أضف البوت", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton(text="📖 التعليمات", callback_data="help")]
    ])
    return kb

# ========= Start =========
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id)
    await msg.answer("أهلاً بك في RADAR 🔥", reply_markup=main_kb())

# ========= Help =========
@dp.callback_query(lambda c: c.data == "help")
async def help_menu(c: types.CallbackQuery):
    text = """
📖 *تعليمات البوت*

بالرد على شخص:
طرد / كتم / الغاء كتم / مسح

🚀 البوت سريع وخفيف
"""
    await c.message.edit_text(text)

# ========= Admin Panel =========
@dp.message(Command("panel"))
async def panel(msg: types.Message):
    if msg.from_user.id != DEV_ID:
        return
    await msg.answer("لوحة التحكم:\n/stats\n/broadcast")

@dp.message(Command("stats"))
async def stats(msg: types.Message):
    if msg.from_user.id != DEV_ID:
        return
    await msg.answer(f"عدد المستخدمين: {len(db['users'])}")

@dp.message(Command("broadcast"))
async def broadcast(msg: types.Message):
    if msg.from_user.id != DEV_ID:
        return

    text = msg.text.replace("/broadcast ", "")
    for user in db["users"]:
        try:
            await bot.send_message(user, text)
            await asyncio.sleep(0.05)
        except:
            pass

# ========= Group Commands =========
@dp.message()
async def group(msg: types.Message):
    if msg.chat.type == "private":
        return

    if not msg.reply_to_message:
        return

    chat_id = msg.chat.id
    user_id = msg.from_user.id
    target = msg.reply_to_message.from_user
    text = (msg.text or "").strip()

    if not await is_admin(chat_id, user_id):
        return

    # منع طرد الأدمن
    if await is_admin(chat_id, target.id):
        await msg.reply("❌ ما تقدر على أدمن")
        return

    try:
        if text == "طرد":
            await bot.ban_chat_member(chat_id, target.id)
            await msg.reply("تم الطرد 🚫")

        elif text == "كتم":
            await bot.restrict_chat_member(
                chat_id,
                target.id,
                ChatPermissions(can_send_messages=False)
            )
            await msg.reply("تم الكتم 🔇")

        elif text == "الغاء كتم":
            await bot.restrict_chat_member(
                chat_id,
                target.id,
                ChatPermissions(can_send_messages=True)
            )
            await msg.reply("تم فك الكتم 🔊")

        elif text == "مسح":
            await bot.delete_message(chat_id, msg.reply_to_message.message_id)
            await bot.delete_message(chat_id, msg.message_id)

    except Exception as e:
        logging.error(e)
        await msg.reply("⚠️ البوت يحتاج صلاحيات")

# ========= Run =========
async def main():
    keep_alive()
    print("BOT STARTED")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

