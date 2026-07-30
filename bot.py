import os
import json
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

# ================= الإعدادات الأساسية =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") # توكن البوت من بيئة ريندر
DEV_ID = 6043858925
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"
BOT_USERNAME = "RA_G_bot" 
BOT_NAME = "RADAR"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ================= نظام حفظ البيانات =================
DATA_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"users": [], "premium": [], "settings": {}}
    return {"users": [], "premium": [], "settings": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

db_data = load_data()

def add_user(user_id):
    if user_id not in db_data["users"]:
        db_data["users"].append(user_id)
        save_data(db_data)

def make_premium(user_id):
    if user_id not in db_data["premium"]:
        db_data["premium"].append(user_id)
        save_data(db_data)

def is_premium(user_id):
    return user_id in db_data["premium"] or user_id == DEV_ID

# ================= سيرفر البقاء (Render Fix) =================
app = Flask('')

@app.route('/')
def home():
    return f"🚀 {BOT_NAME} System is Online!"

def run():
    # هذا السطر مهم جداً لنجاح النشر في Render
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# ================= دوال التحقق =================
def is_subscribed(user_id):
    if user_id == DEV_ID: return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False # إذا لم يكن مشتركاً أو البوت ليس أدمن في القناة

def is_admin(chat_id, user_id):
    if user_id == DEV_ID: return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except:
        return False

# ================= لوحات الأزرار =================
def get_force_sub_keyboard():
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📢 اضغط هنا للاشتراك في القناة", url=CHANNEL_URL))
    kb.row(InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub"))
    return kb

def get_welcome_keyboard(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ أضف البوت إلى مجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.row(
        InlineKeyboardButton("📢 قناة البوت", url=CHANNEL_URL),
        InlineKeyboardButton("🔄 مشاركة", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=أفضل بوت لحماية الجروبات!")
    )
    if not is_premium(user_id):
        kb.add(InlineKeyboardButton("⭐ ترقية إلى RADAR Pro", callback_data="buy_premium"))
    else:
        kb.add(InlineKeyboardButton("👑 أنت تستخدم نسخة Pro", callback_data="premium_info"))
    return kb

def send_welcome_message(chat_id, user_id, first_name):
    badge = "👑 (Pro)" if is_premium(user_id) else "✨ (مجاني)"
    text = (
        f"👋 أهلاً بك يا [{first_name}](tg://user?id={user_id})\n\n"
        f"🛡️ *حالتك:* {badge}\n"
        "🤖 أنا بوت حماية متقدم، أنظف مجموعتك من الروابط والسبام فوراً بصمت.\n\n"
        "💡 *طريقة العمل:*\n"
        "1. أضفني للجروب.\n"
        "2. ارفعني كـ *مشرف*.\n"
        "3. سأعمل تلقائياً!"
    )
    bot.send_message(chat_id, text, reply_markup=get_welcome_keyboard(user_id))

# ================= معالجة جميع رسائل الخاص =================
# هذه الدالة تتفاعل مع /start وأي نص أو صورة أو ملصق يرسله المستخدم في الخاص
@bot.message_handler(func=lambda m: m.chat.type == 'private', content_types=['text', 'photo', 'video', 'document', 'sticker', 'voice'])
def private_messages_handler(message):
    user_id = message.from_user.id
    add_user(user_id)
    
    # إذا لم يكن مشتركاً، نوقفه هنا ونطلب الاشتراك
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ *عذراً، يجب عليك الاشتراك في قناة البوت أولاً.*\n\nاشترك من الزر بالأسفل ثم اضغط (تحقق من الاشتراك) 👇",
            reply_markup=get_force_sub_keyboard()
        )
        return

    # إذا كان مشتركاً، نعرض الترحيب
    send_welcome_message(message.chat.id, user_id, message.from_user.first_name)

# ================= زر التحقق من الاشتراك =================
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.delete_message(call.message.chat.id, call.message.message_id) # مسح رسالة التحذير
        bot.answer_callback_query(call.id, "✅ تم التحقق، شكراً لاشتراكك!")
        send_welcome_message(call.message.chat.id, user_id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ أنت لم تشترك بعد! اشترك ثم اضغط تحقق.", show_alert=True)

# ================= نظام Pro والنجوم =================
@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def callback_buy_premium(call):
    bot.answer_callback_query(call.id)
    
    # رسالة توضيحية لـ RADAR Pro
    pro_info = (
        "💎 *ميزات RADAR Pro:*\n\n"
        "1️⃣ *حصانة تامة:* لن يحذف البوت روابطك أو رسائلك في أي جروب.\n"
        "2️⃣ *أوامر المشرفين:* يمكنك إرسال (قفل الروابط) أو (فتح الروابط) للتحكم بالجروب.\n"
        "3️⃣ *أولوية وسرعة:* استجابة فورية خالية من القيود.\n\n"
        "💳 *الدفع عبر نجوم تيليجرام (مرة واحدة فقط للأبد)* 👇"
    )
    bot.send_message(call.message.chat.id, pro_info)
    
    # إرسال الفاتورة
    bot.send_invoice(
        chat_id=call.message.chat.id,
        title="ترقية RADAR Pro 👑",
        description="احصل على الحصانة وأوامر التحكم الكاملة مدى الحياة.",
        invoice_payload="premium_radar",
        provider_token="", 
        currency="XTR",
        prices=[LabeledPrice("اشتراك Pro دائم", 50)],
        start_parameter="pro_sub"
    )

@bot.callback_query_handler(func=lambda call: call.data == "premium_info")
def callback_premium_info(call):
    bot.answer_callback_query(call.id, "👑 أنت تمتلك نسخة Pro! جميع الميزات مفعلة.", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    make_premium(message.from_user.id)
    bot.send_message(message.chat.id, "🎉 *تم الدفع بنجاح!*\n👑 مبروك، أنت الآن مستخدم Pro وتم تفعيل جميع الميزات.")

# ================= حماية الجروبات =================
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'], content_types=['text', 'photo', 'video', 'document', 'new_chat_members', 'left_chat_member'])
def group_moderation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_str = str(chat_id)
    text = message.text or message.caption or ""

    # مسح رسائل الدخول والخروج
    if message.content_type in ['new_chat_members', 'left_chat_member']:
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        return

    # أوامر Pro / الإدارة (قفل وفتح)
    if is_admin(chat_id, user_id) or is_premium(user_id):
        if text == "قفل الروابط":
            db_data["settings"][chat_str] = "locked"
            save_data(db_data)
            bot.reply_to(message, "🔒 تم قفل الروابط.")
        elif text == "فتح الروابط":
            db_data["settings"][chat_str] = "unlocked"
            save_data(db_data)
            bot.reply_to(message, "🔓 تم السماح بالروابط.")
        return # تخطي الفلترة للأدمن والـ Pro

    # فلترة الروابط للأعضاء العاديين
    if db_data["settings"].get(chat_str, "locked") == "locked" and message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link', 'mention', 'email']:
                try:
                    bot.delete_message(chat_id, message.message_id)
                    return
                except: pass

# ================= تشغيل النظام =================
if __name__ == "__main__":
    keep_alive()
    print(f"🚀 بدء تشغيل {BOT_NAME}...")
    # skip_pending=False : لجعل البوت ينفذ الرسائل اللي وصلته وهو طافي
    bot.infinity_polling(skip_pending=False, timeout=20)

