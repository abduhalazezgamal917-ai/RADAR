import os
import json
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

# ================= الإعدادات =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DEV_ID = int(os.environ.get("DEV_ID", 6043858925))
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"
BOT_USERNAME = "RA_G_bot"
BOT_NAME = "RADAR"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ================= قاعدة البيانات =================
DATA_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"users": [], "settings": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db_data = load_data()

def add_user(user_id):
    if user_id not in db_data["users"]:
        db_data["users"].append(user_id)
        save_data(db_data)

# ================= Render Keep Alive =================
app = Flask('')

@app.route('/')
def home():
    return f"{BOT_NAME} is alive"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    Thread(target=run, daemon=True).start()

# ================= صلاحيات =================
def is_subscribed(user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['creator', 'administrator', 'member']
    except:
        return False

def is_admin(chat_id, user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
        return False

# ================= واجهات =================
def force_sub():
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📢 اشترك بالقناة", url=CHANNEL_URL))
    kb.row(InlineKeyboardButton("🔄 تحقق", callback_data="check"))
    return kb

def welcome_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ أضف البوت", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.add(InlineKeyboardButton("📢 القناة", url=CHANNEL_URL))
    return kb

# ================= الخاص =================
@bot.message_handler(func=lambda m: m.chat.type == "private")
def private(msg):
    user_id = msg.from_user.id
    add_user(user_id)

    if not is_subscribed(user_id):
        bot.send_message(msg.chat.id, "اشترك أولاً", reply_markup=force_sub())
        return

    bot.send_message(msg.chat.id, "أهلاً بك في RADAR 🔥", reply_markup=welcome_kb())

# ================= تحقق =================
@bot.callback_query_handler(func=lambda c: c.data == "check")
def check(c):
    if is_subscribed(c.from_user.id):
        bot.answer_callback_query(c.id, "تم التحقق ✅")
        bot.send_message(c.message.chat.id, "أهلاً بك 🔥")
    else:
        bot.answer_callback_query(c.id, "اشترك أولاً ❌", show_alert=True)

# ================= الحماية =================
@bot.message_handler(func=lambda m: m.chat.type != "private", content_types=['text', 'new_chat_members', 'left_chat_member'])
def group(msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    text = (msg.text or "").strip()

    # حذف دخول وخروج
    if msg.content_type in ['new_chat_members', 'left_chat_member']:
        try: bot.delete_message(chat_id, msg.message_id)
        except: pass
        return

    # أوامر بالرد
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user

        # مسح
        if text == "مسح" and is_admin(chat_id, user_id):
            try:
                bot.delete_message(chat_id, msg.reply_to_message.message_id)
                bot.delete_message(chat_id, msg.message_id)
            except: pass
            return

        # طرد
        if text == "طرد" and is_admin(chat_id, user_id):
            try:
                bot.ban_chat_member(chat_id, target.id)
                bot.reply_to(msg, "تم الطرد 🚫")
            except:
                bot.reply_to(msg, "البوت يحتاج صلاحيات")
            return

        # كتم
        if text == "كتم" and is_admin(chat_id, user_id):
            try:
                bot.restrict_chat_member(
                    chat_id,
                    target.id,
                    ChatPermissions(can_send_messages=False)
                )
                bot.reply_to(msg, "تم الكتم 🔇")
            except:
                bot.reply_to(msg, "فشل التنفيذ")
            return

        # الغاء كتم
        if text == "الغاء كتم" and is_admin(chat_id, user_id):
            try:
                bot.restrict_chat_member(
                    chat_id,
                    target.id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True
                    )
                )
                bot.reply_to(msg, "تم فك الكتم 🔊")
            except:
                bot.reply_to(msg, "فشل التنفيذ")
            return

    # قفل الروابط
    if is_admin(chat_id, user_id):
        if text == "قفل الروابط":
            db_data["settings"][str(chat_id)] = "locked"
            save_data(db_data)
            bot.reply_to(msg, "تم القفل 🔒")
            return

        if text == "فتح الروابط":
            db_data["settings"][str(chat_id)] = "open"
            save_data(db_data)
            bot.reply_to(msg, "تم الفتح 🔓")
            return

    # فلترة الروابط
    if db_data["settings"].get(str(chat_id)) == "locked":
        if msg.entities and not is_admin(chat_id, user_id):
            for e in msg.entities:
                if e.type in ['url', 'text_link']:
                    try:
                        bot.delete_message(chat_id, msg.message_id)
                    except: pass
                    return

# ================= تشغيل =================
if __name__ == "__main__":
    keep_alive()
    print("BOT STARTED")
    bot.infinity_polling()

