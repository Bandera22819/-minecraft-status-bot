import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

SERVER = "claude1488-oHtN.aternos.me:29651"
BOT_TOKEN = "9051358163:AAGadXnGLZPUqPlcZkemxkpmzfa-821jXZw"
STATE_FILE = Path("bot_state.json")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg(method, params=None):
    data = urllib.parse.urlencode(params or {}).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram {method}: {result}")
    return result["result"]


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"offset": 0, "chats": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_server_status():
    url = "https://api.mcsrvstat.us/3/" + urllib.parse.quote(SERVER, safe=":")
    req = urllib.request.Request(url, headers={"User-Agent": "MinecraftTelegramStatusBot/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("online") is False:
        return f"🔴 Сервер: OFFLINE\n👥 Игроки: 0\n🌐 Адрес: {SERVER}"
    if data.get("online") is not True:
        return f"⚠️ Не удалось определить статус сервера\n🌐 Адрес: {SERVER}"
    players = data.get("players") or {}
    online, maximum = players.get("online", "нет данных"), players.get("max")
    count = f"{online}/{maximum}" if maximum is not None and online != "нет данных" else str(online)
    lines = ["🟢 Сервер: ONLINE", f"👥 Игроки: {count}", f"🌐 Адрес: {SERVER}"]
    if data.get("version"):
        lines.append(f"🧩 Версия: {data['version']}")
    return "\n".join(lines)


def send(chat_id, text):
    try:
        tg("sendMessage", {"chat_id": str(chat_id), "text": text})
        return True
    except Exception as exc:
        print(f"Cannot send to {chat_id}: {exc}")
        return False


def command_of(message):
    text = (message.get("text") or "").strip()
    if not text.startswith("/"):
        return ""
    return text.split()[0].split("@")[0].lower()


def main():
    state = load_state()
    chats = set(str(x) for x in state.get("chats", []))
    offset = int(state.get("offset", 0))

    updates = tg("getUpdates", {
        "offset": offset,
        "timeout": 0,
        "allowed_updates": json.dumps(["message", "my_chat_member"]),
    })

    for update in updates:
        state["offset"] = max(int(state.get("offset", 0)), int(update["update_id"]) + 1)

        membership = update.get("my_chat_member")
        if membership:
            chat = membership.get("chat", {})
            chat_id = str(chat.get("id", ""))
            new_status = membership.get("new_chat_member", {}).get("status")
            old_status = membership.get("old_chat_member", {}).get("status")
            if chat_id and chat.get("type") in ("group", "supergroup"):
                if new_status in ("member", "administrator"):
                    chats.add(chat_id)
                    send(chat_id, "✅ Я добавлен в эту группу и включил мониторинг Minecraft.\nКоманды: /status — проверить сейчас, /stop — отключить.")
                elif old_status in ("member", "administrator") and new_status in ("left", "kicked"):
                    chats.discard(chat_id)
            continue

        message = update.get("message") or {}
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))
        command = command_of(message)
        if not chat_id or not command:
            continue

        if command == "/start":
            chats.add(chat_id)
            send(chat_id, "✅ Этот чат подписан на мониторинг Minecraft.\n/status — проверить сейчас\n/stop — отключить подписку")
        elif command == "/status":
            try:
                send(chat_id, get_server_status())
            except Exception as exc:
                send(chat_id, f"⚠️ Ошибка проверки сервера: {type(exc).__name__}: {exc}")
        elif command == "/stop":
            chats.discard(chat_id)
            send(chat_id, "🔕 Мониторинг отключён в этом чате.")
        elif command == "/help":
            send(chat_id, "Команды:\n/start — включить мониторинг\n/status — проверить сервер\n/stop — отключить мониторинг")

    state["chats"] = sorted(chats)
    save_state(state)

    if chats:
        try:
            status = get_server_status()
        except Exception as exc:
            status = f"⚠️ Ошибка проверки Minecraft-сервера\n{type(exc).__name__}: {exc}\n🌐 Адрес: {SERVER}"
        for chat_id in sorted(chats):
            send(chat_id, status)
    print(f"Processed {len(updates)} updates; subscribed chats: {len(chats)}")


if __name__ == "__main__":
    main()
