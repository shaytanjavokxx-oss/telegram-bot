import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from config import *
from database import init_db, order_qoshish, order_olish, status_yangilash, barcha_orderlar

logging.basicConfig(level=logging.INFO)

# Conversation states
XIZMAT, VARIANT, TARGET, SCREENSHOT = range(4)

# Temp data
user_data_temp = {}

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ Telegram Stars", callback_data="xizmat_stars")],
        [InlineKeyboardButton("💎 Telegram Premium", callback_data="xizmat_premium")],
        [InlineKeyboardButton("🎁 Telegram Gift", callback_data="xizmat_gift")],
        [InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalarim")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "Bu bot orqali quyidagi xizmatlarni sotib olishingiz mumkin:\n\n"
        "⭐ Telegram Stars\n"
        "💎 Telegram Premium\n"
        "🎁 Telegram Gift\n\n"
        "Qaysi xizmatni xohlaysiz?",
        reply_markup=reply_markup
    )
    return XIZMAT

# ===================== XIZMAT TANLASH =====================
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
                f"⭐ {v['miqdor']} Stars — {v['narx']:,} so'm",
                callback_data=f"variant_{v['miqdor']}_{v['narx']}"
            )])
    elif xizmat_key == "premium":
        for v in xizmat["variantlar"]:
            keyboard.append([InlineKeyboardButton(
                f"💎 {v['muddat']} — {v['narx']:,} so'm",
                callback_data=f"variant_{v['muddat']}_{v['narx']}"
            )])
    elif xizmat_key == "gift":
        for v in xizmat["variantlar"]:
            keyboard.append([InlineKeyboardButton(
                f"🎁 {v['nomi']} — {v['narx']:,} so'm",
                callback_data=f"variant_{v['nomi']}_{v['narx']}"
            )])

    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="orqaga")])

    await query.edit_message_text(
        f"{xizmat['nomi']} — variant tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return VARIANT

# ===================== VARIANT TANLASH =====================
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
        f"✅ Tanlangan: {variant_nomi}\n"
        f"💰 Narx: {narx:,} so'm\n\n"
        f"📱 Xizmat kimga bo'lsin?\n"
        f"Telegram username yoki telefon raqamini yuboring:\n"
        f"(Masalan: @username yoki +998901234567)"
    )
    return TARGET

# ===================== TARGET USERNAME =====================
async def target_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    target = update.message.text
    user_data_temp[uid]["target"] = target

    narx = user_data_temp[uid]["narx"]

    await update.message.reply_text(
        f"💳 To'lov ma'lumotlari:\n\n"
        f"Karta raqami: <code>{KARTA_RAQAM}</code>\n"
        f"Karta egasi: <b>{KARTA_EGASI}</b>\n\n"
        f"💰 To'lanadigan summa: <b>{narx:,} so'm</b>\n\n"
        f"✅ To'lovni amalga oshirib, <b>screenshot</b> yuboring:",
        parse_mode="HTML"
    )
    return SCREENSHOT

# ===================== SCREENSHOT =====================
async def screenshot_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    username = update.message.from_user.username or str(uid)

    if not update.message.photo:
        await update.message.reply_text("❗ Iltimos, to'lov screenshotini rasm sifatida yuboring.")
        return SCREENSHOT

    data = user_data_temp.get(uid, {})
    xizmat = data.get("xizmat", "")
    variant = data.get("variant", "")
    narx = data.get("narx", 0)
    target = data.get("target", "")

    order_id = order_qoshish(uid, username, xizmat, variant, narx, target)

    # Adminga xabar
    caption = (
        f"🆕 YANGI BUYURTMA #{order_id}\n\n"
        f"👤 Foydalanuvchi: @{username} (ID: {uid})\n"
        f"🛒 Xizmat: {xizmat}\n"
        f"📦 Variant: {variant}\n"
        f"💰 Narx: {narx:,} so'm\n"
        f"🎯 Kimga: {target}\n\n"
        f"✅ Tasdiqlash uchun quyidagi tugmani bosing:"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_ok_{order_id}_{uid}"),
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"admin_no_{order_id}_{uid}")
        ]
    ]

    photo = update.message.photo[-1].file_id
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        f"✅ Buyurtmangiz qabul qilindi! (#{order_id})\n\n"
        f"⏳ Admin tekshirib, tez orada xizmat ko'rsatiladi.\n"
        f"📞 Savollar uchun: {ADMIN_USERNAME}"
    )

    user_data_temp.pop(uid, None)
    return ConversationHandler.END

# ===================== ADMIN PANEL =====================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    parts = query.data.split("_")
    action = parts[1]  # ok yoki no
    order_id = int(parts[2])
    user_id = int(parts[3])

    order = order_olish(order_id)

    if action == "ok":
        status_yangilash(order_id, "tasdiqlandi")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Buyurtmangiz #{order_id} tasdiqlandi!\n\n"
                 f"Xizmat tez orada ko'rsatiladi. Rahmat! 🙏"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ TASDIQLANDI",
            reply_markup=None
        )
    elif action == "no":
        status_yangilash(order_id, "bekor qilindi")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ Buyurtmangiz #{order_id} bekor qilindi.\n\n"
                 f"Savollar uchun: {ADMIN_USERNAME}"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ BEKOR QILINDI",
            reply_markup=None
        )

# ===================== BUYURTMALARIM =====================
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
        await query.edit_message_text("📦 Hozircha buyurtmalaringiz yo'q.")
        return

    text = "📦 So'nggi buyurtmalaringiz:\n\n"
    for r in rows:
        status_emoji = "✅" if r[4] == "tasdiqlandi" else "⏳" if r[4] == "kutilmoqda" else "❌"
        text += f"{status_emoji} #{r[0]} — {r[1]} ({r[2]})\n💰 {r[3]:,} so'm | {r[5]}\n\n"

    await query.edit_message_text(text)

# ===================== ADMIN BUYURTMALAR =====================
async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    rows = barcha_orderlar()
    if not rows:
        await update.message.reply_text("Buyurtmalar yo'q.")
        return

    text = "📋 So'nggi 20 ta buyurtma:\n\n"
    for r in rows:
        text += f"#{r[0]} | {r[2]} | {r[3]} | {r[5]} | {r[8]}\n"

    await update.message.reply_text(text)

# ===================== ORQAGA =====================
async def start_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("⭐ Telegram Stars", callback_data="xizmat_stars")],
        [InlineKeyboardButton("💎 Telegram Premium", callback_data="xizmat_premium")],
        [InlineKeyboardButton("🎁 Telegram Gift", callback_data="xizmat_gift")],
        [InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalarim")],
    ]
    await query.edit_message_text(
        "👋 Qaysi xizmatni xohlaysiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi. /start bosing.")
    return ConversationHandler.END

# ===================== MAIN =====================
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            XIZMAT: [CallbackQueryHandler(xizmat_tanlash)],
            VARIANT: [CallbackQueryHandler(variant_tanlash)],
            TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_olish)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot_olish),
                         MessageHandler(filters.TEXT & ~filters.COMMAND, screenshot_olish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CommandHandler("orders", admin_orders))

    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
