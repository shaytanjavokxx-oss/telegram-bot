import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from config import *
from database import init_db, order_qoshish, order_olish, status_yangilash, barcha_orderlar

logging.basicConfig(level=logging.INFO)

XIZMAT, VARIANT, TARGET, SCREENSHOT = range(4)
user_data_temp = {}

MINI_APP_URL = "https://shaytanjavokxx-oss.github.io/miniapp/miniapp.html"

# ═══════════════════════════════════════
#              /START
# ═══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = user.first_name

    keyboard = [
        [
            InlineKeyboardButton("⭐ Stars", callback_data="xizmat_stars"),
            InlineKeyboardButton("💎 Premium", callback_data="xizmat_premium"),
        ],
        [
            InlineKeyboardButton("🎁 Gift sovg'a", callback_data="xizmat_gift"),
        ],
        [
            InlineKeyboardButton("🛒 Mini App Do'kon", web_app=WebAppInfo(url=MINI_APP_URL)),
        ],
        [
            InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalarim"),
            InlineKeyboardButton("📞 Aloqa", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}"),
        ],
    ]

    text = (
        f"👑 *Assalomu alaykum, {name}!*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🌟 *JONY PREMIUM* xizmatiga xush kelibsiz!\n\n"
        f"📦 *Bizda mavjud xizmatlar:*\n"
        f"⭐ *Stars* — reaktsiya va sovg'alar uchun\n"
        f"💎 *Premium* — Telegram Premium obuna\n"
        f"🎁 *Gift* — do'stingizga maxsus sovg'a\n\n"
        f"📋 *Buyurtma berish tartibi:*\n"
        f"1️⃣ Xizmat turini tanlang\n"
        f"2️⃣ Miqdor yoki muddatni tanlang\n"
        f"3️⃣ Kimga ekanini kiriting\n"
        f"4️⃣ Kartaga to'lov qiling\n"
        f"5️⃣ Screenshot yuboring\n"
        f"6️⃣ Admin tasdiqlaydi ✅\n\n"
        f"⚡ *Bajarish vaqti:* 5—30 daqiqa\n"
        f"🔐 *100% ishonchli va xavfsiz!*\n\n"
        f"👇 Quyidan xizmat tanlang:"
    )

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return XIZMAT


# ═══════════════════════════════════════
#           XIZMAT TANLASH
# ═══════════════════════════════════════
async def xizmat_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buyurtmalarim":
        await buyurtmalarim(update, context)
        return ConversationHandler.END

    xizmat_key = data.replace("xizmat_", "")
    xizmat = XIZMATLAR[xizmat_key]
    user_data_temp[query.from_user.id] = {"xizmat": xizmat_key}

    keyboard = []
    if xizmat_key == "stars":
        for v in xizmat["variantlar"]:
            keyboard.append([InlineKeyboardButton(
                f"⭐ {v['miqdor']} Stars  —  {v['narx']:,} so'm",
                callback_data=f"variant_{v['miqdor']}_{v['narx']}"
            )])
    elif xizmat_key == "premium":
        for v in xizmat["variantlar"]:
            keyboard.append([InlineKeyboardButton(
                f"💎 {v['muddat']}  —  {v['narx']:,} so'm",
                callback_data=f"variant_{v['muddat']}_{v['narx']}"
            )])
    elif xizmat_key == "gift":
        for v in xizmat["variantlar"]:
            keyboard.append([InlineKeyboardButton(
                f"🎁 {v['nomi']}  —  {v['narx']:,} so'm",
                callback_data=f"variant_{v['nomi']}_{v['narx']}"
            )])

    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="orqaga")])

    await query.edit_message_text(
        f"*{xizmat['nomi']}*\n━━━━━━━━━━━━━━━━━━\n\n💡 Quyidan variant tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return VARIANT


# ═══════════════════════════════════════
#           VARIANT TANLASH
# ═══════════════════════════════════════
async def variant_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "orqaga":
        await start_from_query(update, context)
        return XIZMAT

    parts = query.data.replace("variant_", "").rsplit("_", 1)
    variant_nomi = parts[0]
    narx = int(parts[1])

    uid = query.from_user.id
    user_data_temp[uid]["variant"] = variant_nomi
    user_data_temp[uid]["narx"] = narx

    await query.edit_message_text(
        f"✅ *Tanlangan:* {variant_nomi}\n"
        f"💰 *Narx:* {narx:,} so'm\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 *Xizmat kimga bo'lsin?*\n\n"
        f"Telegram username yoki telefon raqamini yuboring:\n"
        f"Masalan: `@username` yoki `+998901234567`",
        parse_mode="Markdown"
    )
    return TARGET


# ═══════════════════════════════════════
#           TARGET OLISH
# ═══════════════════════════════════════
async def target_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    target = update.message.text
    user_data_temp[uid]["target"] = target
    narx = user_data_temp[uid]["narx"]

    await update.message.reply_text(
        f"💳 *To'lov ma'lumotlari:*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏦 Karta raqami:\n"
        f"`{KARTA_RAQAM}`\n\n"
        f"👤 Karta egasi: *{KARTA_EGASI}*\n\n"
        f"💰 To'lanadigan summa: *{narx:,} so'm*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📸 To'lovni amalga oshirib, *screenshot* yuboring:",
        parse_mode="Markdown"
    )
    return SCREENSHOT


# ═══════════════════════════════════════
#           SCREENSHOT OLISH
# ═══════════════════════════════════════
async def screenshot_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user = update.message.from_user
    username = user.username or str(uid)
    name = user.first_name

    if not update.message.photo:
        await update.message.reply_text(
            "❗ Iltimos, to'lov screenshotini *rasm* sifatida yuboring.",
            parse_mode="Markdown"
        )
        return SCREENSHOT

    data = user_data_temp.get(uid, {})
    xizmat = data.get("xizmat", "")
    variant = data.get("variant", "")
    narx = data.get("narx", 0)
    target = data.get("target", "")

    order_id = order_qoshish(uid, username, xizmat, variant, narx, target)

    # Admin ga xabar
    caption = (
        f"🆕 *YANGI BUYURTMA* #{order_id}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Mijoz:* {name} (@{username})\n"
        f"🆔 *ID:* `{uid}`\n\n"
        f"🛒 *Xizmat:* {xizmat}\n"
        f"📦 *Variant:* {variant}\n"
        f"🎯 *Kimga:* {target}\n"
        f"💰 *Narx:* {narx:,} so'm\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⬇️ Tasdiqlash yoki bekor qilish:"
    )

    keyboard = [[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_ok_{order_id}_{uid}"),
        InlineKeyboardButton("❌ Bekor", callback_data=f"admin_no_{order_id}_{uid}")
    ]]

    photo = update.message.photo[-1].file_id
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🔢 Buyurtma raqami: *#{order_id}*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"⏳ Admin tekshirib, *5—30 daqiqa* ichida xizmat ko'rsatiladi.\n\n"
        f"❓ Savol bo'lsa: {ADMIN_USERNAME}",
        parse_mode="Markdown"
    )

    user_data_temp.pop(uid, None)
    return ConversationHandler.END


# ═══════════════════════════════════════
#           ADMIN CALLBACK
# ═══════════════════════════════════════
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    parts = query.data.split("_")
    action = parts[1]
    order_id = int(parts[2])
    user_id = int(parts[3])

    if action == "ok":
        status_yangilash(order_id, "tasdiqlandi")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 *Buyurtmangiz tasdiqlandi!*\n\n"
                 f"🔢 Buyurtma: *#{order_id}*\n"
                 f"━━━━━━━━━━━━━━━━━━\n\n"
                 f"✅ Xizmat tez orada ko'rsatiladi.\n"
                 f"🙏 Rahmat, yana keling!",
            parse_mode="Markdown"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ *TASDIQLANDI*",
            parse_mode="Markdown",
            reply_markup=None
        )

    elif action == "no":
        status_yangilash(order_id, "bekor qilindi")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ *Buyurtmangiz bekor qilindi.*\n\n"
                 f"🔢 Buyurtma: *#{order_id}*\n"
                 f"━━━━━━━━━━━━━━━━━━\n\n"
                 f"❓ Savol bo'lsa: {ADMIN_USERNAME}",
            parse_mode="Markdown"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ *BEKOR QILINDI*",
            parse_mode="Markdown",
            reply_markup=None
        )


# ═══════════════════════════════════════
#           BUYURTMALARIM
# ═══════════════════════════════════════
async def buyurtmalarim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    import sqlite3
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT id, xizmat, variant, narx, status, sana FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 5", (uid,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="orqaga")]]
        await query.edit_message_text(
            "📭 *Hozircha buyurtmalaringiz yo'q.*\n\nXarid qilish uchun orqaga bosing!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = "📦 *So'nggi buyurtmalaringiz:*\n━━━━━━━━━━━━━━━━━━\n\n"
    for r in rows:
        if r[4] == "tasdiqlandi":
            emoji = "✅"
        elif r[4] == "bekor qilindi":
            emoji = "❌"
        else:
            emoji = "⏳"
        text += f"{emoji} *#{r[0]}* — {r[1]} ({r[2]})\n💰 {r[3]:,} so'm | {r[5]}\n\n"

    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="orqaga")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


# ═══════════════════════════════════════
#           ADMIN BUYURTMALAR
# ═══════════════════════════════════════
async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    rows = barcha_orderlar()
    if not rows:
        await update.message.reply_text("📭 Buyurtmalar yo'q.")
        return

    text = "📋 *So'nggi 20 ta buyurtma:*\n━━━━━━━━━━━━━━━━━━\n\n"
    for r in rows:
        if r[8] == "tasdiqlandi":
            emoji = "✅"
        elif r[8] == "bekor qilindi":
            emoji = "❌"
        else:
            emoji = "⏳"
        text += f"{emoji} *#{r[0]}* | @{r[2]} | {r[3]} | {r[5]:,} so'm\n"

    await update.message.reply_text(text, parse_mode="Markdown")


# ═══════════════════════════════════════
#           STATISTIKA
# ═══════════════════════════════════════
async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    import sqlite3
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    jami = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='tasdiqlandi'")
    tasdiqlandi = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='kutilmoqda'")
    kutilmoqda = c.fetchone()[0]
    c.execute("SELECT SUM(narx) FROM orders WHERE status='tasdiqlandi'")
    daromad = c.fetchone()[0] or 0
    conn.close()

    text = (
        f"📊 *STATISTIKA*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 Jami buyurtmalar: *{jami}*\n"
        f"✅ Tasdiqlangan: *{tasdiqlandi}*\n"
        f"⏳ Kutilmoqda: *{kutilmoqda}*\n\n"
        f"💰 Jami daromad: *{daromad:,} so'm*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ═══════════════════════════════════════
#           ORQAGA
# ═══════════════════════════════════════
async def start_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [
            InlineKeyboardButton("⭐ Stars", callback_data="xizmat_stars"),
            InlineKeyboardButton("💎 Premium", callback_data="xizmat_premium"),
        ],
        [
            InlineKeyboardButton("🎁 Gift sovg'a", callback_data="xizmat_gift"),
        ],
        [
            InlineKeyboardButton("🛒 Mini App Do'kon", web_app=WebAppInfo(url=MINI_APP_URL)),
        ],
        [
            InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalarim"),
            InlineKeyboardButton("📞 Aloqa", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}"),
        ],
    ]
    await query.edit_message_text(
        "👑 *JONY PREMIUM*\n━━━━━━━━━━━━━━━━━━\n\n👇 Xizmat tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi. /start bosing.")
    return ConversationHandler.END


# ═══════════════════════════════════════
#               MAIN
# ═══════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            XIZMAT: [CallbackQueryHandler(xizmat_tanlash)],
            VARIANT: [CallbackQueryHandler(variant_tanlash)],
            TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_olish)],
            SCREENSHOT: [
                MessageHandler(filters.PHOTO, screenshot_olish),
                MessageHandler(filters.TEXT & ~filters.COMMAND, screenshot_olish)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CommandHandler("stat", statistika))

    print("✅ JONY PREMIUM Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
