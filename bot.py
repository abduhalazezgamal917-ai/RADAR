import os
import json
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

# ================= الإعدادات الأساسية =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") # تأكد من وضع التوكن في إعدادات Render
DEV_ID = 6043858925
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"
BOT_USERNAME = "RA_G_bot" # عدل هذا ليتطابق مع يوزر بوتك
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
            return {"users": [], "premium": [], "settings": {}}
    return {"users": [], "premium": [], "settings": {}}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

db_data = load_data()
if "settings" not in db_data:
    db_data["settings"] = {}

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

# ================= سيرفر البقاء (Render + UptimeRobot) =================
app = Flask('')

@app.route('/')
def home():
    return f"🚀 {BOT_NAME} System is Online and Running Perfectly!"

def run():
    # ضروري جداً لـ Render لكي لا يغلق السيرفر
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # لجعل الثريد يعمل في الخلفية بدون مشاكل
    t.start()

# ================= دوال التحقق الصارمة =================
def is_subscribed(user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        # إذا كان البوت ليس أدمن في القناة، سيعطي خطأ. تأكد من رفعه كأدمن!
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
    kb.add(InlineKeyboardButton("📢 اضغط هنا للاشتراك في القناة", url=CHANNEL_URL))
    kb.add(InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub"))
    return kb

def get_welcome_keyboard(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ أضف البوت إلى مجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.row(
        InlineKeyboardButton("📢 قناة البوت", url=CHANNEL_URL),
        InlineKeyboardButton("🔄 مشاركة", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=أفضل بوت لحماية الجروبات!")
    )
    if not is_premium_user(user_id):
        kb.add(InlineKeyboardButton("⭐ الترقية إلى (Premium)", callback_data="buy_premium"))
    else:
        kb.add(InlineKeyboardButton("👑 أنت تستخدم النسخة المدفوعة", callback_data="premium_info"))
    return kb

# ================= رسالة الترحيب =================
def send_welcome_message(chat_id, user_id, first_name):
    status_badge = "👑 مستخدم مميز (Premium)" if is_premium_user(user_id) else "✨ مستخدم مجاني"
    welcome_text = (
        f"👋 أهلاً بك يا [{first_name}](tg://user?id={user_id}) في نظام *{BOT_NAME}*!\n\n"
        f"🛡️ *حالتك:* {status_badge}\n\n"
        "🤖 أنا حارس مجموعتك الشخصي، أعمل بكفاءة وسرعة لتنظيف الجروب من:\n"
        "🚫 الروابط، المعرفات، التوجيهات، ورسائل الانضمام المزعجة.\n\n"
        "💡 *طريقة الاستخدام:*\n"
        "1. أضفني للجروب.\n"
        "2. ارفعني كـ *مشرف (Admin)*.\n"
        "3. استرخي، وسأقوم بالباقي بصمت!"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_welcome_keyboard(user_id))

# ================= أوامر البداية والاشتراك =================
@bot.message_handler(commands=['start'])
def start_command(message):
    if message.chat.type != 'private':
        return
        
    user_id = message.from_user.id
    add_user(user_id)
    
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"⚠️ *عذراً عزيزي، لا يمكنك استخدام البوت!*\n\nيجب عليك الاشتراك في قناتنا الرسمية أولاً لتتمكن من تفعيل الخدمات.\nقناة البوت: @{CHANNEL_USERNAME}",
            reply_markup=get_force_sub_keyboard()
        )
        return

    send_welcome_message(message.chat.id, user_id, message.from_user.first_name)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح! شكراً لاشتراكك.", show_alert=False)
        send_welcome_message(call.message.chat.id, user_id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ لم تقم بالاشتراك بعد! اشترك ثم اضغط تحقق مجدداً.", show_alert=True)

# ================= نظام النجوم (Telegram Stars) =================
@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def callback_buy_premium(call):
    bot.answer_callback_query(call.id)
    prices = [LabeledPrice("اشتراك RADAR Premium دائم", 50)]
    bot.send_invoice(
        chat_id=call.message.chat.id,
        title="ترقية RADAR 👑",
        description="ميزات الـ Premium: حصانة من الحذف، تفعيل أوامر إضافية مثل (قفل الروابط)، وتجربة خالية من القيود.",
        invoice_payload="premium_radar_payload",
        provider_token="", # يترك فارغاً لنجوم تيليجرام
        currency="XTR",
        prices=prices,
        start_parameter="premium_sub"
    )

@bot.callback_query_handler(func=lambda call: call.data == "premium_info")
def callback_premium_info(call):
    bot.answer_callback_query(call.id, "👑 أنت تمتلك صلاحيات الـ Premium الكاملة! جميع ميزات البوت مفعلة لديك تلقائياً.", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.from_user.id
    make_premium(user_id)
    bot.send_message(message.chat.id, "🎉 *عملية دفع ناجحة!*\n👑 مبروك! لقد أصبحت الآن من مستخدمي Premium وتم تفعيل جميع الميزات لك بشكل دائم.")

# ================= محرك الحماية والمراقبة (للجروبات) =================

# 1. مسح رسائل الانضمام والمغادرة المزعجة
@bot.message_handler(content_types=['new_chat_members', 'left_chat_member'])
def clean_service_messages(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

# 2. مراقبة النصوص والصور والفيديوهات للحماية
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text', 'photo', 'video', 'document', 'audio', 'animation'])
def group_moderation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_id_str = str(chat_id)
    text = message.text or message.caption or ""

    # أوامر المشرفين السريعة
    if message.reply_to_message:
        if text in ["طرد", "ازالة", "حظر", "كتم"]:
            if is_admin(chat_id, user_id):
                target_user = message.reply_to_message.from_user
                try:
                    if text in ["طرد", "ازالة", "حظر"]:
                        bot.ban_chat_member(chat_id, target_user.id)
                        bot.reply_to(message, f"✅ تم طرد [{target_user.first_name}](tg://user?id={target_user.id}) بنجاح.")
                    elif text == "كتم":
                        bot.restrict_chat_member(chat_id, target_user.id, can_send_messages=False)
                        bot.reply_to(message, f"🔇 تم كتم [{target_user.first_name}](tg://user?id={target_user.id}).")
                    return
                except Exception:
                    bot.reply_to(message, "❌ البوت لا يملك صلاحيات كافية (تأكد من رفعه كمشرف بجميع الصلاحيات).")
                    return

    # أوامر إضافية لمستخدمي Premium والأدمنز
    if is_admin(chat_id, user_id) or is_premium_user(user_id):
        if text == "قفل الروابط":
            db_data["settings"][chat_id_str] = "locked"
            save_data(db_data)
            bot.reply_to(message, "🔒 تم قفل الروابط في هذه المجموعة.")
        elif text == "فتح الروابط":
            db_data["settings"][chat_id_str] = "unlocked"
            save_data(db_data)
            bot.reply_to(message, "🔓 تم السماح بالروابط في هذه المجموعة.")
        # المشرفون وحاملو الـ Premium مستثنون من الفلترة
        return

    # فلترة الروابط والمعرفات للأعضاء العاديين
    links_locked = db_data["settings"].get(chat_id_str, "locked") == "locked"
    
    if links_locked and message.entities:
        for entity in message.entities:
            # حظر الروابط، المعرفات، والإيميلات
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
    # زيادة استقرار الاتصال مع سيرفرات تيليجرام
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=15)

