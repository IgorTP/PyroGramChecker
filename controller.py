import telebot
from telebot import types
import requests

# === Настройки ===
BOT_TOKEN = "ВАШ_ТОКЕН"
CONTROLLER_CHAT_ID = ""

bot = telebot.TeleBot(BOT_TOKEN)

# === Настройка меню ===
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row_width = 1
    markup.add(
        types.KeyboardButton("➕ Добавить пользователя"),
        types.KeyboardButton("➖ Удалить пользователя"),
        types.KeyboardButton("📋 Показать список")
    )
    return markup


# === /start → открываем меню ===
@bot.message_handler(commands=["start"])
def start_handler(message):
    if message.chat.id != CONTROLLER_CHAT_ID:
        bot.reply_to(message, "❌ Доступ запрещён")
        return

    bot.send_message(CONTROLLER_CHAT_ID, "👋 Меню управления ассистентом", reply_markup=get_main_menu())


# === Обработка текстовых сообщений ===
@bot.message_handler(func=lambda m: True)
def handle_buttons(message):
    if message.chat.id != CONTROLLER_CHAT_ID:
        return

    text = message.text.strip()

    if text == "➕ Добавить пользователя":
        bot.send_message(CONTROLLER_CHAT_ID, "Введите юзернейм для добавления:")
        return

    elif text == "➖ Удалить пользователя":
        bot.send_message(CONTROLLER_CHAT_ID, "Введите юзернейм для удаления:")
        return

    elif text == "📋 Показать список":
        send_command("/listuser")
        return

    # Если это обычное сообщение — считаем, что это команда для агента
    if text.startswith("@"):
        username = text.split()[0].lstrip('@')
        command = text.replace(username, '', 1).strip()
        if "добавь" in command.lower() or "включи" in command.lower():
            send_command(f"/adduser {username}")
        elif "удали" in command.lower() or "убери" in command.lower():
            send_command(f"/deluser {username}")
        else:
            send_command(f"/{text}")

    else:
        send_command(f"/command {text}")


# === Функция отправки команды агенту ===
def send_command(command: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CONTROLLER_CHAT_ID,  # ИЛИ chat_id агента
        "text": command,
        "reply_markup": {"force_reply": True}
    }

    try:
        response = requests.post(url, json=data)
        print(f"[Отправлено] {command} | {response.status_code}")
    except Exception as e:
        print(f"[Ошибка при отправке] {e}")


if __name__ == "__main__":
    print("🟢 Интерфейс запущен")
    bot.polling(none_stop=True)