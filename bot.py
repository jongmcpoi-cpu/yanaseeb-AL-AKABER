import os
import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === SETTINGS ===
TOKEN = os.getenv("TOKEN")
ADMIN_IDS = [123456789]   # User ID for Admin
PRICE = 3000
PAYMENT_NUMBER = "32017593"

bot = telebot.TeleBot(TOKEN)

# === Database ===
conn = sqlite3.connect("lottery.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    transaction_id TEXT,
    status TEXT DEFAULT 'pending'
)""")
conn.commit()

# === USER MENU ===
def main_menu():
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🎟️ شراء بطاقة", callback_data="buy_ticket"))
    m.add(InlineKeyboardButton("💰 رصيدي", callback_data="balance"))
    m.add(InlineKeyboardButton("📞 أرقام الدفع", callback_data="payment_info"))
    return m

# === ADMIN MENU ===
def admin_menu():
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("📊 عرض المستخدمين", callback_data="show_users"))
    m.add(InlineKeyboardButton("💸 تعديل الرصيد", callback_data="edit_balance"))
    m.add(InlineKeyboardButton("✅ الموافقة على الشحنات", callback_data="approve_payments"))
    m.add(InlineKeyboardButton("📢 بث رسالة", callback_data="broadcast"))
    return m

# === START ===
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    username = message.from_user.username or "بدون اسم"
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (uid, username))
    conn.commit()

    if uid in ADMIN_IDS:
        bot.send_message(uid, "👋 أهلاً الأدمن!", reply_markup=admin_menu())
    else:
        bot.send_message(uid, "🎉 أهلاً بك في *يانصيب الأكابر*!", reply_markup=main_menu(), parse_mode="Markdown")

# === HANDLERS ===
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    uid = call.from_user.id

    if call.data == "buy_ticket":
        bot.send_message(uid, f"🎟️ سعر البطاقة {PRICE} ل.س\nأرسل: `TransactionID Amount`", parse_mode="Markdown")

    elif call.data == "balance":
        c.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = c.fetchone()[0]
        bot.send_message(uid, f"💰 رصيدك: {bal} ل.س")

    elif call.data == "payment_info":
        bot.send_message(uid, f"📞 أرقام الدفع:\n{PAYMENT_NUMBER}")

    # === ADMIN ACTIONS ===
    elif uid in ADMIN_IDS:

        if call.data == "show_users":
            c.execute("SELECT id, username, balance FROM users")
            users = c.fetchall()
            msg = "\n".join([f"{u[1]} ({u[0]}) — {u[2]} ل.س" for u in users])
            bot.send_message(uid, f"📋 المستخدمون:\n{msg}")

        elif call.data == "edit_balance":
            bot.send_message(uid, "أرسل:\n`UserID NewBalance`", parse_mode="Markdown")

        elif call.data == "approve_payments":
            c.execute("SELECT ticket_id, user_id, amount, transaction_id FROM tickets WHERE status='pending'")
            pending = c.fetchall()
            if not pending:
                bot.send_message(uid, "لا توجد شحنات معلقة.")
            else:
                for t in pending:
                    bot.send_message(uid, f"💠 Ticket: {t[0]}\nUser: {t[1]}\nAmount: {t[2]}\nTX: {t[3]}\n\nللموافقة:\n`approve {t[0]}`\nللرفض:\n`reject {t[0]}`", parse_mode="Markdown")

        elif call.data == "broadcast":
            bot.send_message(uid, "أرسل نص الرسالة ليتم بثها:")

# === MESSAGE HANDLER ===
@bot.message_handler(func=lambda m: True)
def handle_msgs(msg):
    uid = msg.from_user.id
    text = msg.text.split()

    try:
        # ADMIN COMMANDS
        if uid in ADMIN_IDS:

            if text[0].lower() == "approve":
                ticket_id = int(text[1])
                c.execute("SELECT user_id, amount FROM tickets WHERE ticket_id=? AND status='pending'", (ticket_id,))
                t = c.fetchone()

                if t:
                    c.execute("UPDATE tickets SET status='approved' WHERE ticket_id=?", (ticket_id,))
                    c.execute("UPDATE users SET balance=balance+? WHERE id=?", (t[1], t[0]))
                    conn.commit()
                    bot.reply_to(msg, f"✅ تمت الموافقة للمستخدم {t[0]}")
                return

            if text[0].lower() == "reject":
                ticket_id = int(text[1])
                c.execute("UPDATE tickets SET status='rejected' WHERE ticket_id=?", (ticket_id,))
                conn.commit()
                bot.reply_to(msg, f"❌ تم الرفض")
                return

            # BROADCAST
            c.execute("SELECT id FROM users")
            for u in c.fetchall():
                bot.send_message(u[0], msg.text)
            bot.reply_to(msg, "✅ تم الإرسال")
            return

        # USER PAYMENT REQUEST
        if len(text) == 2:
            tid = text[0]
            amount = int(text[1])

            c.execute("INSERT INTO tickets (user_id, amount, transaction_id) VALUES (?, ?, ?)", (uid, amount, tid))
            conn.commit()
            bot.send_message(uid, "✅ تم إرسال طلب الشحن للمراجعة.")
            return

    except:
        bot.reply_to(msg, "❌ الصيغة خاطئة.\nاستخدم: `TransactionID Amount`", parse_mode="Markdown")

bot.infinity_polling()
