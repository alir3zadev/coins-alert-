"""
نسخه‌ی چند-کوینی برای GitHub Actions
هر بار اجرا می‌شود، قیمت همه‌ی کوین‌های لیست‌شده در config.json را با هم
از CoinGecko می‌گیرد و برای هر کوینی که وارد محدوده‌اش شده، پیام تلگرام
جداگانه می‌فرستد.
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


def get_prices(coin_ids):
    """قیمت چند کوین را در یک درخواست از CoinGecko می‌گیرد."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    r = requests.get(
        url,
        params={"ids": ",".join(coin_ids), "vs_currencies": "usd"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["CHAT_ID"]

    cfg = load_json(CONFIG_PATH, {})
    coins = cfg["coins"]  # لیست دیکشنری: coin_id, low_price, high_price

    coin_ids = [c["coin_id"] for c in coins]
    prices = get_prices(coin_ids)

    state = load_json(STATE_PATH, {})

    for coin in coins:
        coin_id = coin["coin_id"]
        low = coin["low_price"]
        high = coin["high_price"]

        if coin_id not in prices:
            print(f"هشدار: کوین '{coin_id}' در پاسخ CoinGecko پیدا نشد.")
            continue

        price = prices[coin_id]["usd"]
        print(f"قیمت {coin_id}: {price} دلار (محدوده: {low} تا {high})")

        coin_state = state.get(coin_id, {"alert_sent": False})
        in_range = low <= price <= high

        if in_range and not coin_state.get("alert_sent"):
            msg = (
                f"🚨 هشدار قیمت!\n"
                f"کوین: {coin_id}\n"
                f"قیمت فعلی: {price} دلار\n"
                f"محدوده تنظیم‌شده: {low} تا {high} دلار"
            )
            send_telegram_message(token, chat_id, msg)
            coin_state["alert_sent"] = True
            print(f"پیام هشدار برای {coin_id} ارسال شد.")
        elif not in_range and coin_state.get("alert_sent"):
            coin_state["alert_sent"] = False
            print(f"{coin_id} از محدوده خارج شد؛ وضعیت ریست شد.")
        else:
            print(f"تغییری برای {coin_id} نیست.")

        state[coin_id] = coin_state

    save_json(STATE_PATH, state)


if __name__ == "__main__":
    main()
