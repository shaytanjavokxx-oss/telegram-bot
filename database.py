import sqlite3
from datetime import datetime

DB_FILE = "orders.db"


def _conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = _conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            xizmat TEXT,
            variant TEXT,
            narx INTEGER,
            target_username TEXT,
            status TEXT DEFAULT "kutilmoqda",
            sana TEXT
        )
    ''')
    # Yangi ustunlar (eski bazaga ham mos — xato bermaydi)
    for col, typ in [("chegirma", "INTEGER DEFAULT 0"),
                     ("promo", "TEXT DEFAULT ''"),
                     ("bonus_used", "INTEGER DEFAULT 0")]:
        try:
            c.execute(f"ALTER TABLE orders ADD COLUMN {col} {typ}")
        except Exception:
            pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            bonus INTEGER DEFAULT 0,
            ref_by INTEGER DEFAULT 0,
            ref_earned INTEGER DEFAULT 0,
            joined TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS promos (
            code TEXT PRIMARY KEY,
            percent INTEGER,
            active INTEGER DEFAULT 1,
            used INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            order_id INTEGER PRIMARY KEY,
            user_id INTEGER,
            stars INTEGER
        )
    ''')
    conn.commit()
    conn.close()


# ═══════════ ORDERS ═══════════

def order_qoshish(user_id, username, xizmat, variant, narx, target_username,
                  chegirma=0, promo="", bonus_used=0):
    conn = _conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (user_id, username, xizmat, variant, narx,
                            target_username, sana, chegirma, promo, bonus_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, xizmat, variant, narx, target_username,
          datetime.now().strftime("%Y-%m-%d %H:%M"), chegirma, promo, bonus_used))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id


def order_olish(order_id):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    row = c.fetchone()
    conn.close()
    return row


def status_yangilash(order_id, status):
    conn = _conn()
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()


def barcha_orderlar():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return rows


def user_orderlari(user_id, limit=5):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT id, xizmat, variant, narx, status, sana FROM orders "
              "WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def tasdiqlangan_soni(user_id):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE user_id=? AND status='tasdiqlandi'",
              (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


# ═══════════ USERS / REFERAL / BONUS ═══════════

def user_qoshish(user_id, username, ref_by=0):
    """Yangi user bo'lsa qo'shadi va True qaytaradi, bor bo'lsa False."""
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = c.fetchone()
    if exists:
        c.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        conn.commit()
        conn.close()
        return False
    c.execute("INSERT INTO users (user_id, username, ref_by, joined) VALUES (?,?,?,?)",
              (user_id, username, ref_by,
               datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return True


def get_user(user_id):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT user_id, username, bonus, ref_by, ref_earned FROM users "
              "WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def bonus_qoshish(user_id, amount, ref_earned=False):
    conn = _conn()
    c = conn.cursor()
    if ref_earned:
        c.execute("UPDATE users SET bonus=bonus+?, ref_earned=ref_earned+? "
                  "WHERE user_id=?", (amount, amount, user_id))
    else:
        c.execute("UPDATE users SET bonus=bonus+? WHERE user_id=?",
                  (amount, user_id))
    conn.commit()
    conn.close()


def bonus_ayirish(user_id, amount):
    conn = _conn()
    c = conn.cursor()
    c.execute("UPDATE users SET bonus=MAX(0, bonus-?) WHERE user_id=?",
              (amount, user_id))
    conn.commit()
    conn.close()


def referal_soni(user_id):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE ref_by=?", (user_id,))
    n = c.fetchone()[0]
    conn.close()
    return n


# ═══════════ PROMOKODLAR ═══════════

def promo_yaratish(code, percent):
    conn = _conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO promos (code, percent, active, used) "
              "VALUES (?, ?, 1, COALESCE((SELECT used FROM promos WHERE code=?), 0))",
              (code.upper(), percent, code.upper()))
    conn.commit()
    conn.close()


def promo_olish(code):
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT code, percent, active, used FROM promos WHERE code=?",
              (code.upper(),))
    row = c.fetchone()
    conn.close()
    return row


def promo_off(code):
    conn = _conn()
    c = conn.cursor()
    c.execute("UPDATE promos SET active=0 WHERE code=?", (code.upper(),))
    conn.commit()
    n = conn.total_changes
    conn.close()
    return n > 0


def promo_ishlatildi(code):
    conn = _conn()
    c = conn.cursor()
    c.execute("UPDATE promos SET used=used+1 WHERE code=?", (code.upper(),))
    conn.commit()
    conn.close()


def promolar():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT code, percent, active, used FROM promos ORDER BY code")
    rows = c.fetchall()
    conn.close()
    return rows


# ═══════════ BAHOLAR ═══════════

def baho_saqlash(order_id, user_id, stars):
    conn = _conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO ratings (order_id, user_id, stars) "
              "VALUES (?, ?, ?)", (order_id, user_id, stars))
    conn.commit()
    conn.close()


def ortacha_baho():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT AVG(stars), COUNT(*) FROM ratings")
    row = c.fetchone()
    conn.close()
    return row


# ═══════════ STATISTIKA ═══════════

def toliq_statistika():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    jami = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='tasdiqlandi'")
    tasdiqlandi = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='kutilmoqda'")
    kutilmoqda = c.fetchone()[0]
    c.execute("SELECT SUM(narx) FROM orders WHERE status='tasdiqlandi'")
    daromad = c.fetchone()[0] or 0
    bugun = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(narx) FROM orders WHERE status='tasdiqlandi' AND sana LIKE ?",
              (bugun + "%",))
    bugun_daromad = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM users")
    userlar = c.fetchone()[0]
    c.execute("SELECT SUM(ref_earned) FROM users")
    ref_jami = c.fetchone()[0] or 0
    conn.close()
    return jami, tasdiqlandi, kutilmoqda, daromad, bugun_daromad, userlar, ref_jami
