import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === إعدادات البوت ===
TOKEN = "ضع_هنا_توكن_البوت"
ADMIN_IDS = [123456789]  # ضع معرف الأدمن هنا
PRICE = 3000
PAYMENT_NUMBER = "32017593"

bot = telebot.TeleBot(TOKEN)

# === إنشاء قاعدة البيانات ===
conn = sqlite3.connect("lottery.db", check_same_thread=False)
c = conn.cursor()

# جدول المستخدمين
c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)""")

# جدول التذاكر / الشحن
c.execute("""CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    transaction_id TEXT,
    status TEXT DEFAULT 'pending'
)""")
conn.commit()

# === واجهة أزرار المستخدمين ===
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎟️ شراء بطاقة", callback_data="buy_ticket"))
    markup.add(InlineKeyboardButton("💰 رصيدي", callback_data="balance"))
    markup.add(InlineKeyboardButton("📞 أرقام الدفع", callback_data="payment_info"))
    return markup

# === واجهة الأدمن ===
def admin_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📊 عرض المستخدمين", callback_data="show_users"))
    markup.add(InlineKeyboardButton("💸 تعديل الرصيد", callback_data="edit_balance"))
    markup.add(InlineKeyboardButton("✅ الموافقة على الشحنات", callback_data="approve_payments"))
    markup.add(InlineKeyboardButton("📢 بث رسالة", callback_data="broadcast"))
    return markup

# === بدء التشغيل ===
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "بدون اسم مستخدم"
    c.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    if user_id in ADMIN_IDS:
        bot.send_message(user_id, "👋 أهلًا بك، أدمن!\nاختر من القائمة:", reply_markup=admin_menu())
    else:
        bot.send_message(user_id, "👋 أهلًا بك في *يانصيب الأكابر*!\nاختر من القائمة:", reply_markup=main_menu(), parse_mode="Markdown")

# === التعامل مع الأزرار ===
@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    user_id = call.from_user.id
    if call.data == "buy_ticket":
        bot.send_message(user_id, f"🎟️ سعر البطاقة: {PRICE} ل.س\nأرسل رقم العملية والمبلغ كالتالي:\n`TransactionID Amount`", parse_mode="Markdown")
    elif call.data == "balance":
        c.execute("SELECT balance FROM users WHERE id=?", (user_id,))
        bal = c.fetchone()[0]
        bot.send_message(user_id, f"💰 رصيدك الحالي: {bal} ل.س")
    elif call.data == "payment_info":
        bot.send_message(user_id, f"🔹 أرقام الدفع:\n📱 {PAYMENT_NUMBER}")
    elif call.data == "show_users" and user_id in ADMIN_IDS:
        c.execute("SELECT id, username, balance FROM users")
        data = c.fetchall()
        msg = "\n".join([f"{u[1]} ({u[0]}) — {u[2]} ل.س" for u in data])
        bot.send_message(user_id, f"📋 قائمة المستخدمين:\n{msg}")
    elif call.data == "edit_balance" and user_id in ADMIN_IDS:
        bot.send_message(user_id, "أرسل رقم المستخدم والمبلغ الجديد بهذا الشكل:\n`123456789 5000`", parse_mode="Markdown")
    elif call.data == "approve_payments" and user_id in ADMIN_IDS:
        c.execute("SELECT ticket_id, user_id, amount, transaction_id FROM tickets WHERE status='pending'")
        pending = c.fetchall()
        if not pending:
            bot.send_message(user_id, "لا توجد شحنات بانتظار الموافقة.")
        else:
            for t in pending:
                bot.send_message(user_id, f"TicketID: {t[0]}, User: {t[1]}, Amount: {t[2]}, TransactionID: {t[3]}\nللموافقة ارسل:\n`approve {t[0]}`\nللرفض ارسل:\n`reject {t[0]}`", parse_mode="Markdown")
    elif call.data == "broadcast" and user_id in ADMIN_IDS:
        bot.send_message(user_id, "أرسل النص الذي تريد بثه لكل المستخدمين:")

# === استقبال الرسائل ===
@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    user_id = message.from_user.id
    try:
        if user_id in ADMIN_IDS:
            text = message.text.split()
            if text[0].lower() == "approve":
                ticket_id = int(text[1])
                c.execute("SELECT user_id, amount FROM tickets WHERE ticket_id=? AND status='pending'", (ticket_id,))
                t = c.fetchone()
                if t:
                    c.execute("UPDATE tickets SET status='approved' WHERE ticket_id=?", (ticket_id,))
                    c.execute("UPDATE users SET balance=balance+? WHERE id=?", (t[1], t[0]))
                    conn.commit()
                    bot.reply_to(message, f"✅ تم اعتماد البطاقة بنجاح للمستخدم {t[0]}")
            elif text[0].lower() == "reject":
                ticket_id = int(text[1])
                c.execute("UPDATE tickets SET status='rejected' WHERE ticket_id=?", (ticket_id,))
                conn.commit()
                bot.reply_to(message, f"❌ تم رفض البطاقة رقم {ticket_id}")
            else:
                # بث رسالة جماعية
                c.execute("SELECT id FROM users")
                users = c.fetchall()
                for u in users:
                    bot.send_message(u[0], message.text)
                bot.reply_to(message, "✅ تم إرسال البث لجميع المستخدمين")
        else:
            # المستخدم يرسل TransactionID + المبلغ
            tid, amount = message.text.split()
            amount = int(amount)
            c.execute("INSERT INTO tickets (user_id, amount, transaction_id) VALUES (?, ?, ?)", (user_id, amount, tid))
            conn.commit()
            bot.send_message(user_id, "✅ تم إرسال طلبك للشحن للمراجعة من قبل الأدمن.")
    except:
        bot.reply_to(message, "❌ صيغة خاطئة. استخدم:\n`TransactionID Amount`", parse_mode="Markdown")

# === التشغيل المستمر ===
bot.infinity_polling()
