import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from config import *
from database import (
    init_db, order_qoshish, order_olish, status_yangilash, barcha_orderlar,
    user_orderlari, tasdiqlangan_soni, user_qoshish, get_user,
    bonus_qoshish, bonus_ayirish, referal_soni,
    promo_yaratish, promo_olish, promo_off, promo_ishlatildi, promolar,
    baho_saqlash, ortacha_baho, toliq_statistika,
)

logging.basicConfig(level=logging.INFO)

XIZMAT, VARIANT, PROMO_SORASH, PROMO_KIRITISH, TARGET, SCREENSHOT = range(6)

user_data_temp = {}

MINI_APP_URL = "https://shaytanjavokxx-oss.github.io/miniapp/miniapp.html"


def esc(t):
    """Markdown buzadigan belgilarni olib tashlaydi (ismlar/usernamelar uchun)."""
    return (str(t).replace("*", "").replace("_", " ")
            .replace("`", "").replace("[", "(").replace("]", ")"))


def doimiy_foiz(user_id):
    """Tasdiqlangan buyurtmalar soniga qarab doimiy mijoz chegirmasi."""
    n = tasdiqlangan_soni(user_id)
    foiz = 0
    for kerak, f in sorted(DOIMIY_CHEGIRMA.items()):
        if n >= kerak:
            foiz = f
    return foiz


def main_keyboard():
    return [
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
            InlineKeyboardButton("👥 Referal — pul ishlash", callback_data="referal_info"),
        ],
        [
            InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalarim"),
            InlineKeyboardButton("📞 Aloqa", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}"),
        ],
    ]


# ═══════════════════════════════════════
# /START (referal bilan)
# ═══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = esc(user.first_name)

    # Referal: /start ref123456
    ref_by = 0
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref"):
            try:
                rid = int(arg[3:])
                if rid != user.id:
                    ref_by = rid
            except ValueError:
                pass

    yangi = user_qoshish(user.id, user.username or "", ref_by)
    if yangi and ref_by:
        try:
            await context.bot.send_message(
                ref_by,
                f"🎉 Sizning havolangiz orqali yangi do'st qo'shildi: {name}!\n"
                f"U har buyurtma qilganda sizga {REF_FOIZ}% bonus tushadi 💰"
            )
        except Exception:
            pass

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
        f"👥 *Referal:* do'st taklif qiling — uning har "
        f"buyurtmasidan *{REF_FOIZ}%* bonus oling!\n\n"
        f"⚡ *Bajarish vaqti:* 5—30 daqiqa\n"
        f"🔐 *100% ishonchli va xavfsiz!*\n\n"
        f"👇 Quyidan xizmat tanlang:"
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(main_keyboard()))
    return XIZMAT


# ═══════════════════════════════════════
# XIZMAT TANLASH
# ═══════════════════════════════════════
async def xizmat_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buyurtmalarim":
        await buyurtmalarim(update, context)
        return XIZMAT

    if data == "referal_info":
        await referal_korsatish(update, context)
        return XIZMAT

    if data == "orqaga":
        await start_from_query(update, context)
        return XIZMAT

    if not data.startswith("xizmat_"):
        return XIZMAT

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
        f"*{xizmat['nomi']}*\n━━━━━━━━━━━━━━━━━━\n\n💡 Quyidan variant tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return VARIANT


# ═══════════════════════════════════════
# VARIANT TANLASH -> PROMOKOD SO'RASH
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
    if uid not in user_data_temp:
        user_data_temp[uid] = {}
    user_data_temp[uid]["variant"] = variant_nomi
    user_data_temp[uid]["narx"] = narx
    user_data_temp[uid]["promo_code"] = ""
    user_data_temp[uid]["promo_foiz"] = 0

    keyboard = [
        [InlineKeyboardButton("🎟 Promokodim bor", callback_data="promo_bor")],
        [InlineKeyboardButton("⏭ Yo'q, davom etish", callback_data="promo_yoq")],
    ]
    await query.edit_message_text(
        f"✅ *Tanlangan:* {esc(variant_nomi)}\n"
        f"💰 *Narx:* {narx:,} so'm\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎟 Promokodingiz bormi?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PROMO_SORASH


async def promo_sorash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "promo_bor":
        await query.edit_message_text(
            "🎟 *Promokodni yozib yuboring:*\n\n"
            "O'tkazib yuborish uchun `yoq` deb yozing.",
            parse_mode="Markdown"
        )
        return PROMO_KIRITISH

    # promo_yoq
    await target_sorash_query(query, context)
    return TARGET


async def promo_kiritish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    kod = update.message.text.strip()

    if kod.lower() in ("yoq", "yo'q", "skip", "-"):
        await target_sorash_msg(update, context)
        return TARGET

    p = promo_olish(kod)
    if not p or not p[2]:
        await update.message.reply_text(
            "❌ Bunday promokod yo'q yoki muddati tugagan.\n"
            "Qaytadan yozing yoki `yoq` deb yozing:",
            parse_mode="Markdown"
        )
        return PROMO_KIRITISH

    user_data_temp[uid]["promo_code"] = p[0]
    user_data_temp[uid]["promo_foiz"] = p[1]
    await update.message.reply_text(
        f"✅ Promokod qabul qilindi: *{p[0]}* — *{p[1]}%* chegirma!",
        parse_mode="Markdown"
    )
    await target_sorash_msg(update, context)
    return TARGET


async def target_sorash_query(query, context):
    await query.edit_message_text(
        "📱 *Xizmat kimga bo'lsin?*\n\n"
        "Telegram username yoki telefon raqamini yuboring:\n"
        "Masalan: `@username` yoki `+998901234567`",
        parse_mode="Markdown"
    )


async def target_sorash_msg(update, context):
    await update.message.reply_text(
        "📱 *Xizmat kimga bo'lsin?*\n\n"
        "Telegram username yoki telefon raqamini yuboring:\n"
        "Masalan: `@username` yoki `+998901234567`",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════
# TARGET OLISH -> TO'LOV (chegirmalar bilan)
# ═══════════════════════════════════════
async def target_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    target = update.message.text
    if uid not in user_data_temp or "narx" not in user_data_temp[uid]:
        await update.message.reply_text("❌ Xatolik. /start dan qayta boshlang.")
        return ConversationHandler.END

    d = user_data_temp[uid]
    d["target"] = target
    narx = d["narx"]

    # Chegirmalarni hisoblash
    promo_foiz = d.get("promo_foiz", 0)
    loyal_foiz = doimiy_foiz(uid)
    jami_foiz = min(promo_foiz + loyal_foiz, 25)  # maksimal 25%

    narx_chegirma = narx * (100 - jami_foiz) // 100
    narx_chegirma = narx_chegirma // 100 * 100  # 100 so'mgacha yaxlitlash

    # Bonus balansdan ishlatish
    u = get_user(uid)
    bonus_bor = u[2] if u else 0
    bonus_used = min(bonus_bor, narx_chegirma)
    final = narx_chegirma - bonus_used

    d["loyal_foiz"] = loyal_foiz
    d["bonus_used"] = bonus_used
    d["final"] = final

    text = (
        f"💳 *To'lov ma'lumotlari:*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏦 Karta raqami:\n"
        f"`{KARTA_RAQAM}`\n\n"
        f"👤 Karta egasi: *{KARTA_EGASI}*\n\n"
        f"💰 Narx: {narx:,} so'm\n"
    )
    if promo_foiz:
        text += f"🎟 Promokod: -{promo_foiz}%\n"
    if loyal_foiz:
        text += f"⭐ Doimiy mijoz: -{loyal_foiz}%\n"
    if bonus_used:
        text += f"👥 Bonus balans: -{bonus_used:,} so'm\n"
    text += (
        f"\n✅ *To'lanadigan summa: {final:,} so'm*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📸 To'lovni amalga oshirib, *screenshot* yuboring:"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return SCREENSHOT


# ═══════════════════════════════════════
# SCREENSHOT OLISH
# ═══════════════════════════════════════
async def screenshot_olish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user = update.message.from_user
    username = esc(user.username or str(uid))
    name = esc(user.first_name)

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
    final = data.get("final", narx)
    target = esc(data.get("target", ""))
    promo_code = data.get("promo_code", "")
    bonus_used = data.get("bonus_used", 0)

    # Bonusni hisobdan yechamiz (rad etilsa qaytariladi)
    if bonus_used:
        bonus_ayirish(uid, bonus_used)
    if promo_code:
        promo_ishlatildi(promo_code)

    order_id = order_qoshish(uid, user.username or str(uid), xizmat, variant,
                             final, data.get("target", ""),
                             chegirma=narx - final, promo=promo_code,
                             bonus_used=bonus_used)

    caption = (
        f"🆕 *YANGI BUYURTMA* #{order_id}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Mijoz:* {name} (@{username})\n"
        f"🆔 *ID:* `{uid}`\n\n"
        f"🛒 *Xizmat:* {xizmat}\n"
        f"📦 *Variant:* {esc(variant)}\n"
        f"🎯 *Kimga:* {target}\n"
        f"💰 *To'lagan:* {final:,} so'm"
    )
    if narx != final:
        caption += f" (asl: {narx:,})"
    if promo_code:
        caption += f"\n🎟 Promo: {promo_code}"
    if bonus_used:
        caption += f"\n👥 Bonus ishlatildi: {bonus_used:,} so'm"
    caption += "\n\n━━━━━━━━━━━━━━━━━━\n⬇️ Tasdiqlash yoki bekor qilish:"

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
# ADMIN CALLBACK (tasdiqlash/bekor + referal bonus + baho + kanal)
# ═══════════════════════════════════════
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    await query.answer()

    parts = query.data.split("_")
    action = parts[1]
    order_id = int(parts[2])
    user_id = int(parts[3])

    if action == "ok":
        status_yangilash(order_id, "tasdiqlandi")
        order = order_olish(order_id)
        narx = order[5] if order else 0

        # Referal bonus
        u = get_user(user_id)
        if u and u[3]:
            ref_id = u[3]
            bon = narx * REF_FOIZ // 100
            if bon > 0:
                bonus_qoshish(ref_id, bon, ref_earned=True)
                try:
                    await context.bot.send_message(
                        ref_id,
                        f"💰 Referal bonus: +{bon:,} so'm!\n"
                        f"Taklif qilgan do'stingiz buyurtma qildi. "
                        f"Balans: /referal"
                    )
                except Exception:
                    pass

        # Baho so'rash tugmalari
        baho_kb = [[
            InlineKeyboardButton("⭐1", callback_data=f"rate_{order_id}_1"),
            InlineKeyboardButton("⭐2", callback_data=f"rate_{order_id}_2"),
            InlineKeyboardButton("⭐3", callback_data=f"rate_{order_id}_3"),
            InlineKeyboardButton("⭐4", callback_data=f"rate_{order_id}_4"),
            InlineKeyboardButton("⭐5", callback_data=f"rate_{order_id}_5"),
        ]]
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 *Buyurtmangiz tasdiqlandi!*\n\n"
                     f"🔢 Buyurtma: *#{order_id}*\n"
                     f"━━━━━━━━━━━━━━━━━━\n\n"
                     f"✅ Xizmat tez orada ko'rsatiladi.\n"
                     f"👥 Do'st taklif qilib pul ishlang: /referal\n\n"
                     f"⭐ Xizmatimizga baho bering:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(baho_kb)
            )
        except Exception:
            pass

        # Kanalga avto-post
        if CHANNEL_ID:
            try:
                await context.bot.send_message(
                    CHANNEL_ID,
                    f"✅ Buyurtma #{order_id} muvaffaqiyatli bajarildi!\n"
                    f"🛒 {order[3]} | {order[4]}\n\n"
                    f"Siz ham buyurtma bering: @{BOT_USERNAME}"
                )
            except Exception:
                pass

        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ *TASDIQLANDI*",
                parse_mode="Markdown",
                reply_markup=None
            )
        except Exception:
            pass

    elif action == "no":
        status_yangilash(order_id, "bekor qilindi")
        # Ishlatilgan bonusni qaytarish
        order = order_olish(order_id)
        if order and len(order) > 11 and order[11]:
            bonus_qoshish(user_id, order[11])
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ *Buyurtmangiz bekor qilindi.*\n\n"
                     f"🔢 Buyurtma: *#{order_id}*\n"
                     f"━━━━━━━━━━━━━━━━━━\n\n"
                     f"💰 Ishlatilgan bonuslaringiz qaytarildi.\n"
                     f"❓ Savol bo'lsa: {ADMIN_USERNAME}",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        try:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ *BEKOR QILINDI*",
                parse_mode="Markdown",
                reply_markup=None
            )
        except Exception:
            pass


# ═══════════════════════════════════════
# BAHO CALLBACK
# ═══════════════════════════════════════
async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    parts = query.data.split("_")
    order_id, stars = int(parts[1]), int(parts[2])
    baho_saqlash(order_id, query.from_user.id, stars)
    await query.answer("Rahmat! 🙏")
    try:
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            query.from_user.id,
            f"🙏 Bahoyingiz uchun rahmat: {'⭐' * stars}\n"
            f"Yana kutamiz!"
        )
    except Exception:
        pass


# ═══════════════════════════════════════
# REFERAL
# ═══════════════════════════════════════
async def referal_korsatish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    user_qoshish(uid, query.from_user.username or "")
    u = get_user(uid)
    bonus = u[2] if u else 0
    earned = u[4] if u else 0
    dostlar = referal_soni(uid)
    link = f"https://t.me/{BOT_USERNAME}?start=ref{uid}"

    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="orqaga")]]
    await query.edit_message_text(
        f"👥 *REFERAL DASTURI*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Do'stingizni taklif qiling — uning *har bir* "
        f"buyurtmasidan *{REF_FOIZ}%* bonus oling!\n"
        f"Bonus keyingi xaridingizda avtomatik chegirma bo'ladi.\n\n"
        f"🔗 *Sizning havolangiz:*\n`{link}`\n\n"
        f"👥 Takliflar: *{dostlar} ta*\n"
        f"💰 Jami ishlangan: *{earned:,} so'm*\n"
        f"💳 Hozirgi balans: *{bonus:,} so'm*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def referal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    user_qoshish(uid, update.message.from_user.username or "")
    u = get_user(uid)
    bonus = u[2] if u else 0
    earned = u[4] if u else 0
    dostlar = referal_soni(uid)
    link = f"https://t.me/{BOT_USERNAME}?start=ref{uid}"
    await update.message.reply_text(
        f"👥 *REFERAL DASTURI*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"Do'stingizni taklif qiling — uning *har bir* "
        f"buyurtmasidan *{REF_FOIZ}%* bonus oling!\n\n"
        f"🔗 *Sizning havolangiz:*\n`{link}`\n\n"
        f"👥 Takliflar: *{dostlar} ta*\n"
        f"💰 Jami ishlangan: *{earned:,} so'm*\n"
        f"💳 Hozirgi balans: *{bonus:,} so'm*",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════
# BUYURTMALARIM
# ═══════════════════════════════════════
async def buyurtmalarim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    rows = user_orderlari(uid, 5)

    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="orqaga")]]
    if not rows:
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
        text += f"{emoji} *#{r[0]}* — {r[1]} ({esc(r[2])})\n💰 {r[3]:,} so'm | {r[5]}\n\n"

    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ═══════════════════════════════════════
# ADMIN BUYRUQLARI
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
        if r[7] == "tasdiqlandi":
            emoji = "✅"
        elif r[7] == "bekor qilindi":
            emoji = "❌"
        else:
            emoji = "⏳"
        text += f"{emoji} *#{r[0]}* | @{esc(r[2])} | {r[3]} | {r[5]:,} so'm\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    jami, tasdiqlandi, kutilmoqda, daromad, bugun_d, userlar, ref_jami = toliq_statistika()
    avg, baho_soni = ortacha_baho()
    avg_txt = f"{avg:.1f} ⭐ ({baho_soni} ta)" if avg else "hali yo'q"
    text = (
        f"📊 *STATISTIKA*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Foydalanuvchilar: *{userlar}*\n"
        f"📦 Jami buyurtmalar: *{jami}*\n"
        f"✅ Tasdiqlangan: *{tasdiqlandi}*\n"
        f"⏳ Kutilmoqda: *{kutilmoqda}*\n\n"
        f"💰 Jami daromad: *{daromad:,} so'm*\n"
        f"📅 Bugungi daromad: *{bugun_d:,} so'm*\n"
        f"👥 Referal bonuslar: *{ref_jami:,} so'm*\n"
        f"⭐ O'rtacha baho: *{avg_txt}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def promo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /promo KOD FOIZ — yangi promokod yaratish."""
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "Foydalanish: /promo KOD FOIZ\nMasalan: /promo YANGI10 10")
        return
    kod = context.args[0].upper()
    try:
        foiz = int(context.args[1])
        if not 1 <= foiz <= 50:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Foiz 1 dan 50 gacha bo'lsin.")
        return
    promo_yaratish(kod, foiz)
    await update.message.reply_text(
        f"✅ Promokod yaratildi: *{kod}* — {foiz}% chegirma\n\n"
        f"Kanalingizda e'lon qiling!",
        parse_mode="Markdown"
    )


async def promolar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    rows = promolar()
    if not rows:
        await update.message.reply_text("Promokodlar yo'q. Yaratish: /promo KOD FOIZ")
        return
    text = "🎟 *Promokodlar:*\n\n"
    for code, percent, active, used in rows:
        holat = "🟢" if active else "🔴"
        text += f"{holat} *{code}* — {percent}% | ishlatildi: {used} marta\n"
    text += "\nO'chirish: /promooff KOD"
    await update.message.reply_text(text, parse_mode="Markdown")


async def promooff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Foydalanish: /promooff KOD")
        return
    ok = promo_off(context.args[0])
    await update.message.reply_text("✅ O'chirildi." if ok else "Topilmadi.")


# ═══════════════════════════════════════
# ORQAGA
# ═══════════════════════════════════════
async def start_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "👑 *JONY PREMIUM*\n━━━━━━━━━━━━━━━━━━\n\n👇 Xizmat tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(main_keyboard())
    )


async def orqaga_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start_from_query(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp.pop(update.message.from_user.id, None)
    await update.message.reply_text("❌ Bekor qilindi. /start bosing.")
    return ConversationHandler.END


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════
def main():
    init_db()
    app = (Application.builder()
           .token(BOT_TOKEN)
           .connect_timeout(30).read_timeout(30).write_timeout(30)
           .build())

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            XIZMAT: [CallbackQueryHandler(xizmat_tanlash)],
            VARIANT: [CallbackQueryHandler(variant_tanlash)],
            PROMO_SORASH: [CallbackQueryHandler(promo_sorash)],
            PROMO_KIRITISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, promo_kiritish)],
            TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, target_olish)],
            SCREENSHOT: [
                MessageHandler(filters.PHOTO, screenshot_olish),
                MessageHandler(filters.TEXT & ~filters.COMMAND, screenshot_olish)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate_"))
    app.add_handler(CallbackQueryHandler(orqaga_global, pattern="^orqaga$"))
    app.add_handler(CommandHandler("referal", referal_cmd))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CommandHandler("stat", statistika))
    app.add_handler(CommandHandler("promo", promo_cmd))
    app.add_handler(CommandHandler("promolar", promolar_cmd))
    app.add_handler(CommandHandler("promooff", promooff_cmd))

    print("✅ JONY PREMIUM Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
