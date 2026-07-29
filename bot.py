import os
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

# ================= الإعدادات الأساسية =================
# لا نحتاج سوى التوكن فقط!
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DEV_ID = 6043858925
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = "https://t.me/ZenoX_Tools"
BOT_USERNAME = "RA_G_bot"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ================= سيرفر البقاء (Keep-Alive لـ UptimeRobot) =================
app = Flask('')

@app.route('/')
def home():
    return "ZenoX Guard System is Online and Running! 🚀"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= دوال التحقق =================
def is_subscribed(user_id):
    if user_id == DEV_ID:
        return True
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
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

def get_welcome_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ أضف البوت إلى مجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.row(
        InlineKeyboardButton("📢 قناة البوت", url=CHANNEL_URL),
        InlineKeyboardButton("🔄 مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=أفضل بوت لحماية الجروبات من الروابط والازعاج!")
    )
    kb.add(InlineKeyboardButton("⭐ ترقية إلى النسخة المدفوعة", callback_data="buy_premium"))
    return kb

# ================= نظام الرسائل الخاصة (الترحيب والاشتراك) =================
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def private_handler(message):
    user_id = message.from_user.id
    
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id,
            f"⚠️ *عذراً، عليك الاشتراك في قناة البوت أولاً.*\n\nقناة البوت: @{CHANNEL_USERNAME}",
            reply_markup=get_force_sub_keyboard()
        )
        return

    welcome_text = (
        f"👋 أهلاً بك يا [{message.from_user.first_name}](tg://user?id={user_id}) في *ZenoX Guard*!\n\n"
        "🛡️ أنا بوت متخصص في حماية مجموعتك بكفاءة عالية وسرعة خارقة.\n"
        "🚫 أقوم بحذف الروابط، المعرفات، والسبام فوراً دون تدخل منك.\n\n"
        "💡 *طريقة الاستخدام:*\n"
        "1. أضفني إلى مجموعتك عبر الزر بالأسفل.\n"
        "2. ارفعني كـ *مشرف (Admin)* بصلاحية حذف الرسائل وحظر المستخدمين.\n"
        "3. سأبدأ العمل تلقائياً بصمت!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_welcome_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        bot.send_message(call.message.chat.id, "✅ *تم التحقق بنجاح!* أرسل /start لعرض القائمة الرئيسية.")
    else:
        bot.answer_callback_query(call.id, "❌ لم تقم بالاشتراك بعد! اشترك ثم حاول مجدداً.", show_alert=True)

# ================= نظام النجوم (Telegram Stars) =================
@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def callback_buy_premium(call):
    bot.answer_callback_query(call.id)
    prices = [LabeledPrice("اشتراك Premium", 50)]
    bot.send_invoice(
        chat_id=call.message.chat.id,
        title="ترقية ZenoX Guard 👑",
        description="احصل على ميزات مدفوعة مثل: تخصيص أوامر الحذف، رسالة ترحيب خاصة، وإلغاء القيود.",
        invoice_payload="premium_zenox_payload",
        provider_token="", # النجوم لا تحتاج بروفايدر
        currency="XTR",
        prices=prices,
        start_parameter="premium_sub"
    )

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id, "🎉 *شكراً لك! تم الدفع بنجاح.*\n👑 لقد أصبحت الآن من مستخدمي Premium وتم تفعيل جميع الميزات لك.")

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
    if is_admin(chat_id, user_id):
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
    print("🚀 بدء تشغيل بوت ZenoX عبر Telebot...")
    bot.infinity_polling()



