import base64
import os

# === Локальная генерация сессии ===
with open("edit_tracker.session", "rb") as f:
    encoded = base64.b64encode(f.read()).decode()
encoded += '=' * (-len(encoded) % 4)


# === Разбиваем на части ===
def split_session_string(session_string: str, chunk_size: int = 8_000):
    return [session_string[i:i + chunk_size] for i in range(0, len(session_string), chunk_size)]


parts = split_session_string(encoded)

# === Выводим для копирования в Railway ===
print(f"SESSION_PART_COUNT={len(parts)}")
for idx, part in enumerate(parts):
    print(f"SESSION_PART_{idx}={part}")
