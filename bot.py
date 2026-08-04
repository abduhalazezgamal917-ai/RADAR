import os
import json
from flask import Flask
from threading import Thread
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

================= الإعدادات الأساسية =================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DEV_ID = int(os.environ.get("DEV_ID", 6043858925))
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = f"https://t.me/{CHANNEL_USERNAME}"
BOT_USERNAME = "RA_G_bot"
BOT_NAME = "RADAR"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

================= نظام حفظ البيانات =================

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

================= سيرفر البقاء (Render Fix) =================

app = Flask('')

@app.route('/')
def home():
return f"🚀 {BOT_NAME} System is Online!"

def run():
port = int(os.environ.get('PORT', 8080))
app.run(host='0.0.0.0', port=port)

def keep_alive():
t = Thread(target=run, daemon=True)
t.start()

================= دوال التحقق =================

def is_subscribed(user_id):
if user_id == DEV_ID: return True
try:
member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
return member.status in ['creator', 'administrator', 'member']
except:
return False

def is_admin(chat_id, user_id):
if user_id == DEV_ID: return True
try:
member = bot.get_chat_member(chat_id, user_id)
return member.status in ['creator', 'administrator']
except:
return False

================= لوحات الأزرار =================

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
kb.add(InlineKeyboardButton("📖 التعليمات (كيف يعمل البوت؟)", callback_data="instructions"))

if not is_premium(user_id):  
    kb.add(InlineKeyboardButton("⭐ ترقية إلى RADAR Pro", callback_data="buy_premium"))  
else:  
    kb.add(InlineKeyboardButton("👑 أنت تستخدم نسخة Pro", callback_data="premium_info"))  
return kb

def get_back_keyboard():
kb = InlineKeyboardMarkup()
kb.add(InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="back_home"))
return kb

def send_welcome_message(chat_id, user_id, first_name):
badge = "👑 (Pro)" if is_premium(user_id) else "✨ (مجاني)"
text = (
f"👋 أهلاً بك يا {first_name}\n\n"
f"🛡️ حالتك: {badge}\n"
"🤖 أنا بوت حماية متقدم، أنظف مجموعتك من الروابط والسبام فوراً بصمت.\n\n"
"💡 طريقة العمل:\n"
"1. أضفني للجروب.\n"
"2. ارفعني كـ مشرف.\n"
"3. سأعمل تلقائياً!"
)
bot.send_message(chat_id, text, reply_markup=get_welcome_keyboard(user_id))

================= معالجة رسائل الخاص =================

@bot.message_handler(func=lambda m: m.chat.type == 'private', content_types=['text', 'photo', 'video', 'document', 'sticker', 'voice'])
def private_messages_handler(message):
user_id = message.from_user.id
add_user(user_id)

if not is_subscribed(user_id):  
    bot.send_message(  
        message.chat.id,  
        "⚠️ *عذراً، يجب عليك الاشتراك في قناة البوت أولاً.*\n\nاشترك من الزر بالأسفل ثم اضغط (تحقق من الاشتراك) 👇",  
        reply_markup=get_force_sub_keyboard()  
    )  
    return  

send_welcome_message(message.chat.id, user_id, message.from_user.first_name)

================= أزرار الواجهة =================

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
user_id = call.from_user.id
if is_subscribed(user_id):
bot.delete_message(call.message.chat.id, call.message.message_id)
bot.answer_callback_query(call.id, "✅ تم التحقق، شكراً لاشتراكك!")
send_welcome_message(call.message.chat.id, user_id, call.from_user.first_name)
else:
bot.answer_callback_query(call.id, "❌ أنت لم تشترك بعد! اشترك ثم اضغط تحقق.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "instructions")
def callback_instructions(call):
text = (
"📖 دليل تعليمات RADAR 📖\n\n"
"✨ النسخة المجانية (للمشرفين فقط):\n"
"• تنظيف صامت لتنبيهات الدخول والخروج.\n"
"• فلترة الروابط والمعرفات التلقائية.\n"
"• إعدادات الجروب: قفل الروابط | فتح الروابط.\n"
"• أمر مميز: مسح (بالرد على أي رسالة لحذفها فوراً).\n\n"
"👑 نسخة RADAR Pro (للمشتركين):\n"
"• حصانة تامة: البوت لا يحذف رسائلك أبداً في أي جروب.\n"
"• أوامر متقدمة (تعمل بالرد على رسالة العضو): \n"
"  ➔ طرد : لحظر وطرد العضو من الجروب.\n"
"  ➔ كتم : لمنع العضو من إرسال رسائل.\n"
"  ➔ الغاء كتم : للسماح للعضو بالكتابة مجدداً.\n\n"
"💡 ملاحظة: أوامر Pro تعمل لك في أي جروب حتى لو لم تكن مشرفاً به!"
)
bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_back_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def callback_back_home(call):
user_id = call.from_user.id
badge = "👑 (Pro)" if is_premium(user_id) else "✨ (مجاني)"
text = (
f"👋 أهلاً بك يا {call.from_user.first_name}\n\n"
f"🛡️ حالتك: {badge}\n"
"🤖 أنا بوت حماية متقدم، أنظف مجموعتك من الروابط والسبام فوراً بصمت.\n\n"
"💡 طريقة العمل:\n"
"1. أضفني للجروب.\n"
"2. ارفعني كـ مشرف.\n"
"3. سأعمل تلقائياً!"
)
bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_welcome_keyboard(user_id))

================= نظام Pro والنجوم =================

@bot.callback_query_handler(func=lambda call: call.data == "buy_premium")
def callback_buy_premium(call):
bot.answer_callback_query(call.id)
pro_info = (
"💎 ميزات RADAR Pro:\n\n"
"1️⃣ حصانة تامة: لن يحذف البوت روابطك أو رسائلك في أي جروب.\n"
"2️⃣ أوامر المشرفين: يمكنك إرسال (طرد، كتم، قفل، فتح) والتحكم الكامل.\n"
"3️⃣ أولوية وسرعة: استجابة فورية خالية من القيود.\n\n"
"💳 الدفع عبر نجوم تيليجرام (مرة واحدة فقط للأبد) 👇"
)
bot.send_message(call.message.chat.id, pro_info)
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
bot.answer_callback_query(call.id, "👑 أنت تمتلك نسخة Pro! جميع الميزات والأوامر مفعلة.", show_alert=True)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
bot.answer_pre_checkout_query(query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
make_premium(message.from_user.id)
bot.send_message(message.chat.id, "🎉 تم الدفع بنجاح!\n👑 مبروك، أنت الآن مستخدم Pro وتم تفعيل جميع الميزات.")

================= حماية الجروبات وأوامر المشرفين (التعديل الجوهري هنا) =================

@bot.message_handler(func=lambda m: m.chat.type != 'private', content_types=['text', 'photo', 'video', 'document', 'new_chat_members', 'left_chat_member'])
def group_moderation(message):
chat_id = message.chat.id
user_id = message.from_user.id
chat_str = str(chat_id)
text = (message.text or message.caption or "").strip()

# مسح رسائل الدخول والخروج بصمت  
if message.content_type in ['new_chat_members', 'left_chat_member']:  
    try: bot.delete_message(chat_id, message.message_id)  
    except: pass  
    return  

# 1. أوامر الرد السريعة (تتطلب الرد على رسالة)  
if message.reply_to_message:  
    target_user = message.reply_to_message.from_user  
      
    # أمر (مسح)  
    if text == "مسح" and (is_admin(chat_id, user_id) or is_premium(user_id)):  
        try:  
            bot.delete_message(chat_id, message.reply_to_message.message_id)  
            bot.delete_message(chat_id, message.message_id)  
        except: pass  
        return  

    # أوامر Pro (طرد، كتم، الغاء كتم)  
    if text in ["طرد", "كتم", "الغاء كتم"]:  
        if is_premium(user_id) or is_admin(chat_id, user_id):  
            try:  
                if text == "طرد":  
                    bot.ban_chat_member(chat_id, target_user.id)  
                    bot.reply_to(message, f"🚨 تم طرد [{target_user.first_name}](tg://user?id={target_user.id}) بنجاح.")  
                elif text == "كتم":  
                    bot.restrict_chat_member(chat_id, target_user.id, can_send_messages=False)  
                    bot.reply_to(message, f"🔇 تم كتم [{target_user.first_name}](tg://user?id={target_user.id}).")  
                elif text == "الغاء كتم":  
                    bot.restrict_chat_member(chat_id, target_user.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)  
                    bot.reply_to(message, f"🔊 تم إلغاء كتم [{target_user.first_name}](tg://user?id={target_user.id}).")  
            except Exception:  
                bot.reply_to(message, "❌ البوت لا يملك صلاحيات كافية لعمل هذا التعديل.")  
        else:  
            bot.reply_to(message, "👑 عذراً، هذا الأمر مخصص للمشرفين أو مستخدمي RADAR Pro فقط!")  
        return  

# 2. أوامر إعدادات الجروب (قفل الروابط / فتح الروابط)  
if is_admin(chat_id, user_id) or is_premium(user_id):  
    if text == "قفل الروابط":  
        db_data["settings"][chat_str] = "locked"  
        save_data(db_data)  
        bot.reply_to(message, "🔒 تم قفل الروابط بنجاح في هذا الجروب.")  
        return  
    elif text == "فتح الروابط":  
        db_data["settings"][chat_str] = "unlocked"  
        save_data(db_data)  
        bot.reply_to(message, "🔓 تم السماح بالروابط بنجاح في هذا الجروب.")  
        return  

# 3. فلترة الروابط للأعضاء العاديين  
if db_data["settings"].get(chat_str, "locked") == "locked" and message.entities:  
    if not (is_admin(chat_id, user_id) or is_premium(user_id)):  
        for entity in message.entities:  
            if entity.type in ['url', 'text_link', 'mention', 'email']:  
                try:  
                    bot.delete_message(chat_id, message.message_id)  
                    return  
                except: pass

================= تشغيل النظام =================

if name == "main":
keep_alive()
print(f"🚀 بدء تشغيل {BOT_NAME}...")
bot.infinity_polling(skip_pending=False, timeout=20)
