import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    Message, 
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery
)
from pyrogram.enums import ChatMemberStatus, MessageEntityType
from pyrogram.errors import UserNotParticipant

from keep_alive import keep_alive 

# ================= الإعدادات الأساسية (عبر متغيرات البيئة لـ Render) =================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ================= بياناتك الثابتة =================
DEV_ID = 6043858925
CHANNEL_USERNAME = "ZenoX_Tools"
CHANNEL_URL = "https://t.me/ZenoX_Tools"
BOT_USERNAME = "RA_G_bot"

app = Client("ZenoX_Guard", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

premium_users = [DEV_ID] 

# ================= دوال التحقق =================
async def is_subscribed(client: Client, user_id: int) -> bool:
    if user_id == DEV_ID: return True
    try:
        member = await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    except Exception: return False

async def is_admin(message: Message) -> bool:
    if message.from_user.id == DEV_ID: return True
    member = await message.chat.get_member(message.from_user.id)
    return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]

# ================= لوحات الأزرار =================
force_sub_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("اضغط هنا للاشتراك في القناة 🚀", url=CHANNEL_URL)],
    [InlineKeyboardButton("التحقق 🔍", callback_data="check_sub")]
])

welcome_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ أضف البوت إلى مجموعتك", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
    [
        InlineKeyboardButton("📢 قناة البوت", url=CHANNEL_URL),
        InlineKeyboardButton("🔄 مشاركة البوت", url=f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=أفضل بوت لحماية الجروبات من الروابط والازعاج!")
    ],
    [InlineKeyboardButton("⭐ ترقية إلى النسخة المدفوعة", callback_data="buy_premium")]
])

# ================= نظام الرسائل الخاصة (الترحيب والاشتراك) =================
@app.on_message(filters.private & filters.incoming & ~filters.service)
async def private_messages_handler(client: Client, message: Message):
    subscribed = await is_subscribed(client, message.from_user.id)
    
    if not subscribed:
        await message.reply_text(
            "⚠️ **عذراً، عليك الاشتراك في قناة البوت أولاً.**\n\n"
            f"قناة البوت: @{CHANNEL_USERNAME}",
            reply_markup=force_sub_keyboard
        )
        return

    welcome_text = (
        f"👋 أهلاً بك يا {message.from_user.mention} في **ZenoX Guard**!\n\n"
        "🛡️ أنا بوت متخصص في حماية مجموعتك بكفاءة عالية وسرعة خارقة.\n"
        "🚫 أقوم بحذف الروابط، المعرفات، والسبام فوراً دون تدخل منك.\n\n"
        "💡 **طريقة الاستخدام:**\n"
        "1. أضفني إلى مجموعتك عبر الزر بالأسفل.\n"
        "2. ارفعني كـ **مشرف (Admin)** بصلاحية حذف الرسائل وحظر المستخدمين.\n"
        "3. سأبدأ العمل تلقائياً بصمت!"
    )
    await message.reply_text(welcome_text, reply_markup=welcome_keyboard)

@app.on_callback_query(filters.regex("check_sub"))
async def check_subscription_callback(client: Client, callback_query: CallbackQuery):
    subscribed = await is_subscribed(client, callback_query.from_user.id)
    if subscribed:
        await callback_query.message.delete()
        await client.send_message(
            callback_query.message.chat.id, 
            "✅ **تم التحقق بنجاح!** أرسل /start لعرض القائمة الرئيسية."
        )
    else:
        await callback_query.answer("❌ لم تقم بالاشتراك بعد! اشترك ثم حاول مجدداً.", show_alert=True)

# ================= نظام الدفع بنجوم تيليجرام =================
@app.on_callback_query(filters.regex("buy_premium"))
async def trigger_premium_invoice(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await client.send_invoice(
        chat_id=callback_query.from_user.id,
        title="ترقية ZenoX Guard 👑",
        description="احصل على ميزات مدفوعة مثل: تخصيص أوامر الحذف، رسالة ترحيب خاصة، وإلغاء القيود.",
        payload="premium_zenox_payload", 
        currency="XTR", 
        prices=[LabeledPrice("اشتراك Premium", 50)], 
        start_parameter="premium_sub"
    )

@app.on_pre_checkout_query()
async def pre_checkout_handler(client: Client, query: PreCheckoutQuery):
    await client.answer_pre_checkout_query(query.id, ok=True)

@app.on_message(filters.successful_payment)
async def successful_payment_handler(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in premium_users:
        premium_users.append(user_id)
    
    await message.reply_text(
        "🎉 **شكراً لك! تم الدفع بنجاح.**\n"
        "👑 لقد أصبحت الآن من مستخدمي Premium وتم تفعيل جميع الميزات الخارقة لك."
    )

# ================= محرك المراقبة والحماية (الجروبات) =================
@app.on_message(filters.group & ~filters.me)
async def group_moderation_engine(client: Client, message: Message):
    # 1. نظام تنفيذ الأوامر للمشرفين (طرد / ازالة)
    if message.text and message.reply_to_message:
        if message.text in ["طرد", "ازالة", "حظر"]:
            if await is_admin(message):
                target_user = message.reply_to_message.from_user
                try:
                    await client.ban_chat_member(message.chat.id, target_user.id)
                    await message.reply_text(f"✅ تم طرد العضو: {target_user.mention} بنجاح.")
                    return
                except Exception:
                    await message.reply_text("❌ حدث خطأ، تأكد أن البوت يمتلك صلاحية الحظر.")
                    return

    # 2. نظام فلترة الروابط والمعرفات
    if message.entities:
        if await is_admin(message):
            return 
        
        forbidden_types = [MessageEntityType.URL, MessageEntityType.TEXT_LINK, MessageEntityType.MENTION]
        for entity in message.entities:
            if entity.type in forbidden_types:
                try:
                    await message.delete()
                    break 
                except Exception:
                    pass

# ================= تشغيل النظام =================
if __name__ == "__main__":
    keep_alive()
    print("🚀 بدء تشغيل نظام حماية ZenoX...")
    app.run()


