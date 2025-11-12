def is_admin(user_id, admin_ids):
    return user_id in admin_ids

def send_admin_notification(bot, admin_ids, user_id, tx_id, amount):
    for admin in admin_ids:
        bot.send_message(admin, f"🧾 عملية جديدة من المستخدم {user_id}:\n"
                                f"رمز العملية: {tx_id}\nالمبلغ: {amount} ل.س")
