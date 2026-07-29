import os
import json
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

# ================= الإعدادات الأساسية =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DEV_ID = 6043858925
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = "https://t.me/ZenoX_Tools"
BOT_USERNAME = "RA_G_bot"
BOT_NAME = "RADAR"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ================= نظام حفظ البيانات (حفظ دائم) =================
DATA_FILE = "users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": [], "premium": []}
    return {"users": [], "premium": []}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
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

def is_premium_user(user_id):
    return user_id in db_data["premium"] or user_id == DEV_ID

# ================= سيرفر البقاء (Keep-Alive لـ Render) =================
app = Flask('')

@app.route('/')
def home():
    return f"{BOT_NAME} System is Online and Running! 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= دوال التحقق الصارمة =================
def is_subscribed(user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        # التأكد أن العضو ليس مغادراً أو محظوراً
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        # إذا لم يكن مشتركاً أو حدث خطأ في جلب العضو، يعتبر غير مشترك
        return False

def is_admin(chat_id, user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# ================= لوحات الأزرار =================
def get_force_sub_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("اضغط هنا للاشتراك في القناة 🚀", url=CHANNEL_URL))
    kb.add(InlineKeyboardButton("التحقق 🔍", callback_data="check_sub"))
    return kb

def get_welcome_keyboard(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ أضف البوت إلى مجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.row(
        InlineKeyboardButton("📢 قناة البوت", url=CHANNEL_URL),
        InlineKeyboardButton("🔄 مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=أفضل بوت لحماية الجروبات وإدارتها بكفاءة عالية!")
    )
    if not is_premium_user(user_id):
        kb.add(InlineKeyboardButton("⭐ ترقية إلى النسخة المدفوعة (Premium)", callback_data="buy_premium"))
    else:
        kb.add(InlineKeyboardButton("👑 أنت تستخدم النسخة المدفوعة", callback_data="premium_info"))
    return kb

# ================= دالة إرسال الترحيب =================
def send_welcome_message(chat_id, user_id, first_name):
    status_badge = "👑 (مستخدم مميز)" if is_premium_user(user_id) else "✨ (نسخة مجانية)"
    welcome_text = (
        f"👋 أهلاً بك يا [{first_name}](tg://user?id={user_id}) في بوت *{BOT_NAME}*!\n\n"
        f"🛡️ حالتك الحالية: {status_badge}\n"
        "🤖 أنا بوت متخصص في حماية مجموعتك بكفاءة عالية وسرعة خارقة.\n"
        "🚫 أقوم بحذف الروابط، المعرفات، والسبام فوراً دون تدخل منك.\n\n"
        "💡 *طريقة الاستخدام:*\n"
        "1. أضفني إلى مجموعتك عبر الزر بالأسفل.\n"
        "2. ارفعني كـ *مشرف (Admin)* بصلاحية حذف الرسائل وحظر المستخدمين.\n"
        "3. سأبدأ العمل تلقائياً بصمت!"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_welcome_keyboard(user_id))

# ================= معالجة أمر /start والرسائل الخاصة =================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    add_user(user_id)
    
    # فحص الاشتراك الإجباري أولاً وقبل كل شيء
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"⚠️ *عذراً، عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه.*\n\nقناة البوت: @{CHANNEL_USERNAME}",
            reply_markup=get_force_sub_keyboard()
        )
        return

    # إذا كان مشتركاً، نعرض له الترحيب فوراً
    send_welcome_message(message.chat.id, user_id, message.from_user.first_name)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome_message(call.message.chat.id, user_id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ لم تقم بالاشتراك بعد في القناة! اشترك ثم اضغط تحقق مجدداً.", show_alert=True)

# ================= نظام النجوم (Telegram Stars) =================
@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def callback_buy_premium(call):
    bot.answer_callback_query(call.id)
    prices = [LabeledPrice("اشتراك RADAR Premium", 50)]
    bot.send_invoice(
        chat_id=call.message.chat.id,
        title="ترقية RADAR 👑",
        description="احصل على ميزات مدفوعة مثل: تخصيص أوامر الحذف، رسالة ترحيب خاصة، وإلغاء القيود.",
        invoice_payload="premium_radar_payload",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="premium_sub"
    )

@bot.callback_query_handler(func=lambda call: call.data == "premium_info")
def callback_premium_info(call):
    bot.answer_callback_query(call.id, "أنت تمتلك صلاحيات الـ Premium الكاملة على هذا البوت! 🚀", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.from_user.id
    make_premium(user_id)
    bot.send_message(message.chat.id, "🎉 *شكراً لك! تم الدفع بنجاح.*\n👑 لقد أصبحت الآن من مستخدمي Premium وتم تفعيل جميع الميزات لك بشكل دائم.")

# ================= محرك المراقبة والحماية (الجروبات) =================
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text', 'caption'])
def group_moderation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text or message.caption or ""

    # 1. أوامر المشرفين (طرد / ازالة)
    if message.reply_to_message and text in ["طرد", "ازالة", "حظر"]:
        if is_admin(chat_id, user_id):
            target_user = message.reply_to_message.from_user
            try:
                bot.ban_chat_member(chat_id, target_user.id)
                bot.reply_to(message, f"✅ تم طرد العضو بنجاح.")
                return
            except Exception:
                bot.reply_to(message, "❌ حدث خطأ، تأكد أن البوت يمتلك صلاحية الحظر.")
                return

    # 2. فلترة الروابط والمعرفات
    if is_admin(chat_id, user_id) or is_premium_user(user_id):
        return

    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link', 'mention', 'email']:
                try:
                    bot.delete_message(chat_id, message.message_id)
                    return
                except Exception:
                    pass

# ================= تشغيل النظام =================
if __name__ == "__main__":
    keep_alive()
    print(f"🚀 بدء تشغيل بوت {BOT_NAME} بنجاح تام...")
    bot.infinity_polling(skip_pending=True)
