import os
import json
from datetime import datetime
import base64
from pyrogram import Client, filters
from dotenv import load_dotenv
import pytz

# Загружаем .env, если он есть
try:
    load_dotenv()
except Exception as e:
    print(e)

# ===== Настройки =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MY_USER_ID = int(os.getenv("MY_USER_ID"))
CONTROLLER_BOT = os.getenv("CONTROLLER_BOT")

PART_COUNT = int(os.getenv("SESSION_PART_COUNT"))
SESSION_PATH = "edit_tracker.session"


# === Восстановление сессии из переменных среды ===
def restore_session_from_parts():
    if not PART_COUNT:
        print("⚠️ SESSION_PART_COUNT не задан")
        return False

    try:
        session_string = ''.join([
            os.getenv(f"SESSION_PART_{i}") for i in range(PART_COUNT)
        ])
        session_string += '=' * (-len(session_string) % 4)

        decoded = base64.b64decode(session_string)
        with open(SESSION_PATH, "wb") as f:
            f.write(decoded)
        print("✅ Сессия восстановлена")
        return True
    except Exception as e:
        print(f"❌ Не удалось восстановить сессию: {e}")
        return False


print("🔄 Попытка восстановить сессию...")
success = restore_session_from_parts()

if not success or not os.path.exists(SESSION_PATH):
    print("❌ Нет сессии. Запуск невозможен.")
    exit(1)

# # === Проверяем наличие сессии до старта ===
# if os.path.exists(SESSION_PATH):
#     print("✅ Сессия найдена")
# else:
#     print("🔄 Попытка восстановить сессию...")
#     success = restore_session_from_parts()
#
#     if not success or not os.path.exists(SESSION_PATH):
#         print("❌ Нет сессии. Запуск невозможен.")
#         exit(1)

original_messages = {}
ALLOWED_USERS_FILE = "allowed_users.json"

# ===== Загрузка обновленного списка =====
if os.path.exists(ALLOWED_USERS_FILE):
    with open(ALLOWED_USERS_FILE, "r") as file:
        ALLOWED_USERS = set(json.load(file))
else:
    ALLOWED_USERS = set()


# ===== Сохранение текущего состояния списка =====
def save_updated_allowed_users():
    with open(ALLOWED_USERS_FILE, "w") as file:
        json.dump(list(ALLOWED_USERS), file)


def convert_to_msk(date: datetime) -> str:
    """Конвертирует время из UTC в MSK и возвращает строку без tzinfo"""
    timezone = pytz.timezone('Europe/Moscow')
    msk_time = date.astimezone(timezone)
    return msk_time.strftime("%Y-%m-%d %H:%M:%S")


# Создаем клиент
app = Client("edit_tracker", api_id=API_ID, api_hash=API_HASH)

# ===== Функции для управления списком пользователей прямого отслеживания =====
base_filters = filters.text & filters.private & filters.me & filters.chat(chats=CONTROLLER_BOT)


@app.on_message(base_filters & filters.command("adduser"))
async def adduser_handler(client, message):
    username = message.text.split(maxsplit=1)[1].strip().lstrip("@")

    ALLOWED_USERS.add(username)
    await message.reply(f"✅ @{username} добавлен в список прямого отслеживания.")
    save_updated_allowed_users()


@app.on_message(base_filters & filters.command("deluser"))
async def deluser_handler(client, message):
    username = message.text.split(maxsplit=1)[1].strip().lstrip("@")
    if username in ALLOWED_USERS:
        ALLOWED_USERS.remove(username)
        await message.reply(f"❌ @{username} удалён из списка прямого отслеживания.")
    else:
        await message.reply(f"⚠️ @{username} не найден в списке.")
    save_updated_allowed_users()


@app.on_message(base_filters & filters.command("listuser"))
async def listuser_handler(client, message):
    if not ALLOWED_USERS:
        await message.reply("📂 Список пуст.")
    else:
        users_list = "\n".join([f"@{us}" for us in ALLOWED_USERS])
        await message.reply(f"📋 Пользователи прямого отслеживания:\n{users_list}")


# ===== Вспомогательная функция для формирования сообщения =====
def format_message(user, chat, original_text, new_text, date_str):
    return f"""
👤 Пользователь: {user.first_name} {user.last_name or ''}
🔗 Юзернейм: {f"@{user.username}" if user.username else "отсутствует"}
🆔 ID пользователя: {user.id}
☎️ Номер телефона: {user.phone_number}
💬 Чат: {chat.title or 'Личное сообщение'}
📅 Дата: {date_str}
📩 Сообщение было изменено:
🔹 До: `{original_text}`
🔸 После: `{new_text}`
"""


# ===== Обработка новых сообщений =====
@app.on_message(filters.text & ~filters.me)
async def save_original(client, message):
    message_id = message.id
    original_messages[message_id] = message.text


# ===== Обработка изменённых сообщений =====
@app.on_edited_message(filters.text & ~filters.me)
async def track_edit(client, message):
    message_id = message.id
    original_text = original_messages.get(message_id)
    new_text = message.text

    if not original_text or new_text == original_text:
        return

    user = message.from_user
    chat = message.chat
    date_str = convert_to_msk(message.date)

    # Формируем сообщение
    formatted_msg = format_message(user, chat, original_text, new_text, date_str)

    if user.username in ALLOWED_USERS:
        await message.reply_text(formatted_msg, quote=True)

    # Отправляем себе в личку
    try:
        await app.send_message(chat_id=CONTROLLER_BOT, text=formatted_msg)
    except Exception as e:
        print(f"[Ошибка при отправке]: {e}")

    # Обновляем текст в истории
    original_messages[message_id] = new_text


if __name__ == "__main__":
    print("🚀 Бот запущен: отслеживание изменений сообщений")
    app.run()
