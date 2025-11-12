import sqlite3

def init_db():
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    # جدول المعاملات
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tx_id TEXT,
        amount INTEGER,
        approved INTEGER DEFAULT 0
    )""")
    # جدول الأرصدة
    c.execute("""CREATE TABLE IF NOT EXISTS balances (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def add_transaction(user_id, tx_id, amount):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, tx_id, amount) VALUES (?, ?, ?)", (user_id, tx_id, amount))
    conn.commit()
    conn.close()

def approve_transaction(tx_id):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT user_id, amount FROM transactions WHERE tx_id=? AND approved=0", (tx_id,))
    row = c.fetchone()
    if row:
        user_id, amount = row
        c.execute("UPDATE transactions SET approved=1 WHERE tx_id=?", (tx_id,))
        c.execute("INSERT INTO balances (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance=balance+?", (user_id, amount, amount))
    conn.commit()
    conn.close()
    return bool(row)

def get_balance(user_id):
    conn = sqlite3.connect("lottery.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM balances WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0
