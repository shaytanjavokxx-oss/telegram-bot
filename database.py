import sqlite3
from datetime import datetime

DB_FILE = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
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
    conn.commit()
    conn.close()

def order_qoshish(user_id, username, xizmat, variant, narx, target_username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (user_id, username, xizmat, variant, narx, target_username, sana)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, xizmat, variant, narx, target_username, datetime.now().strftime("%Y-%m-%d %H:%M")))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def order_olish(order_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    row = c.fetchone()
    conn.close()
    return row

def status_yangilash(order_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

def barcha_orderlar():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return rows
