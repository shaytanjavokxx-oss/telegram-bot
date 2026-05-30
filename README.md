# Telegram Bot — Stars, Premium, Gift Sotish

## O'rnatish

1. Python o'rnating (3.10+)
2. Kutubxona o'rnating:
   ```
   pip install -r requirements.txt
   ```

3. `config.py` faylini oching va BOT_TOKEN ni o'zgartiring:
   ```python
   BOT_TOKEN = "bu yerga @BotFather dan olgan tokeningizni yozing"
   ```

## Botni ishga tushirish

```bash
python bot.py
```

## Bot qanday ishlaydi?

1. Foydalanuvchi /start bosadi
2. Xizmat tanlaydi (Stars / Premium / Gift)
3. Variant tanlaydi (miqdor/muddat)
4. Kimga ekanini yozadi (@username)
5. Karta raqamiga pul o'tkazadi
6. Screenshot yuboradi
7. Siz (admin) screenshotni ko'rasiz va ✅ Tasdiqlash bosasiz
8. Foydalanuvchiga xabar ketadi

## Admin buyruqlari

- `/orders` — so'nggi buyurtmalarni ko'rish

## Fayllar

- `bot.py` — asosiy bot
- `config.py` — sozlamalar (token, karta, narxlar)
- `database.py` — buyurtmalar bazasi (SQLite)
- `orders.db` — avtomatik yaratiladi
