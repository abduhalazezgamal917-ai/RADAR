# ================= واجهات =================
def welcome_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ أضف البوت", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.row(
        InlineKeyboardButton("📢 القناة", url=CHANNEL_URL),
        InlineKeyboardButton("📖 التعليمات", callback_data="help")
    )
    return kb


def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="back"))
    return kb


# ================= التعليمات =================
@bot.callback_query_handler(func=lambda c: c.data == "help")
def help_menu(c):
    text = """
📖 *طريقة استخدام بوت RADAR:*

1️⃣ أضف البوت إلى مجموعتك  
2️⃣ ارفع البوت مشرف (Admin)  
3️⃣ البوت يبدأ حماية تلقائيًا 🔥  

🛡️ *ماذا يفعل البوت؟*
- حذف الروابط 🚫  
- تنظيف السبام 🧹  
- إدارة المجموعة بسهولة  

👮‍♂️ *أوامر الأدمن:*
- `طرد` (بالرد على الشخص)
- `مسح` (لحذف رسالة)

⚠️ تأكد أن البوت عنده صلاحيات كاملة!
"""

    bot.edit_message_text(
        text,
        c.message.chat.id,
        c.message.message_id,
        reply_markup=back_kb()
    )


# ================= رجوع =================
@bot.callback_query_handler(func=lambda c: c.data == "back")
def back_home(c):
    bot.edit_message_text(
        "أهلاً بك في RADAR 🔥",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=welcome_kb()
    )

