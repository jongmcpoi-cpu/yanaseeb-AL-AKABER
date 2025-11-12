from telebot import types
from database import approve_transaction

def admin_menu(bot, chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ اعتماد عملية", "💳 تغيير رقم الدفع", "📢 بث رسالة")
    bot.send_message(chat_id, "🛠️ لوحة الإدارة:", reply_markup=markup)

def handle_admin_message(bot, message):
    if message.text == "✅ اعتماد عملية":
        bot.send_message(message.chat.id, "أرسل رمز العملية للموافقة:")
    elif message.text == "💳 تغيير رقم الدفع":
        bot.send_message(message.chat.id, "أرسل الرقم الجديد:")
    elif message.text == "📢 بث رسالة":
        bot.send_message(message.chat.id, "أرسل الرسالة التي تريد بثها للمستخدمين:")
    else:
        if approve_transaction(message.text):
            bot.send_message(message.chat.id, "✅ تمت الموافقة على العملية.")
        else:
            bot.send_message(message.chat.id, "⚠️ لم يتم العثور على العملية أو تمت الموافقة مسبقًا.")
