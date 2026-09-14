"""
نسخه‌ی تک‌اجرا برای GitHub Actions
هر بار که اجرا بشه، یک‌بار قیمت رو چک می‌کنه و در صورت نیاز پیام تلگرام می‌فرسته.
توکن و chat_id از GitHub Secrets (متغیرهای محیطی) خونده می‌شه، نه از فایل.
"""

import json
import os
import requests

CONFIG_PATH = "config.json"
STATE_PATH = "state.json"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.get(url, params={"chat_id": chat_id, "text": text}, timeout=15)
    r.raise_for_status()


def get_price(coin_id):
    url = "https://api.coingecko.com/api/v3/simple/price"
    r = requests.get(url, params={"ids": coin_id, "vs_currencies": "usd"}, timeout=15)
    r.raise_for_status()
    data = r.json()
    if coin_id not in data:
        raise ValueError(f"کوین با شناسه '{coin_id}' در CoinGecko پیدا نشد.")
    return data[coin_id]["usd"]


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    cfg = load_json(CONFIG_PATH, {})
    coin_id = cfg["coin_id"]
    low = cfg["low_price"]
    high = cfg["high_price"]

    state = load_json(STATE_PATH, {"alert_sent": False})

    price = get_price(coin_id)
    print(f"قیمت فعلی {coin_id}: {price} دلار (محدوده: {low} تا {high})")

    in_range = low <= price <= high

    if in_range and not state.get("alert_sent"):
        msg = (
            f"🚨 هشدار قیمت!\n"
            f"کوین: {coin_id}\n"
            f"قیمت فعلی: {price} دلار\n"
            f"محدوده تنظیم‌شده: {low} تا {high} دلار"
        )
        send_telegram_message(token, chat_id, msg)
        state["alert_sent"] = True
        print("پیام هشدار ارسال شد.")
    elif not in_range and state.get("alert_sent"):
        # وقتی قیمت از محدوده خارج شد، ریست می‌کنیم تا دفعه بعد که وارد شد دوباره خبر بده
        state["alert_sent"] = False
        print("قیمت از محدوده خارج شد؛ وضعیت ریست شد.")
    else:
        print("تغییری برای اطلاع‌رسانی نیست.")

    save_json(STATE_PATH, state)


if __name__ == "__main__":
    main()
