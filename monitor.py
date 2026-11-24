import json
import os
import urllib.parse
import urllib.request

SERVER = "claude1488-oHtN.aternos.me:29651"
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


def get_server_status():
    url = "https://api.mcsrvstat.us/3/" + urllib.parse.quote(SERVER, safe=":")
    req = urllib.request.Request(url, headers={"User-Agent": "MinecraftTelegramStatusBot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data.get("online") is False:
        return f"🔴 Сервер: OFFLINE\n👥 Игроки: 0\n🌐 Адрес: {SERVER}"
    if data.get("online") is not True:
        return f"⚠️ Не удалось определить статус сервера\n🌐 Адрес: {SERVER}"

    players = data.get("players") or {}
    online = players.get("online", "нет данных")
    maximum = players.get("max")
    players_text = f"{online}/{maximum}" if maximum is not None and online != "нет данных" else str(online)
    lines = ["🟢 Сервер: ONLINE", f"👥 Игроки: {players_text}", f"🌐 Адрес: {SERVER}"]
    if data.get("version"):
        lines.append(f"🧩 Версия: {data['version']}")
    return "\n".join(lines)


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


if __name__ == "__main__":
    try:
        message = get_server_status()
    except Exception as exc:
        message = f"⚠️ Ошибка проверки Minecraft-сервера\n{type(exc).__name__}: {exc}\n🌐 Адрес: {SERVER}"
    send_telegram(message)
    print(message)
  
