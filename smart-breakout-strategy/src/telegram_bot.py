import os
from typing import Dict

from telegram import Bot


def _load_settings() -> Dict:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "settings.json")
    import json

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_channel_username(channel_username: str) -> str:
    raw = (channel_username or "").strip()
    if "t.me/" in raw:
        seg = raw.split("t.me/")[-1].strip().strip("/")
        if not seg.startswith("@"):
            return f"@{seg}"
        return seg
    return raw


def send_telegram_message(message: str) -> None:
    """Reads Telegram bot_token and channel_username from config and sends the message.
    Prints a confirmation with the target channel.
    """
    settings = _load_settings()
    tg = (settings.get("telegram") or {})
    bot_token = tg.get("bot_token", "")
    channel_username = tg.get("channel_username", "")
    if not bot_token or not channel_username:
        print("Telegram settings missing. Ensure bot_token and channel_username are set in config/settings.json")
        return

    target = _normalize_channel_username(channel_username)
    bot = Bot(token=bot_token)
    bot.send_message(chat_id=target, text=message, disable_web_page_preview=True)
    print(f"📢 Telegram notification sent to {target}")


if __name__ == "__main__":
    # Convenience entrypoint to send the test message
    try:
        # Import lazily to avoid circular imports
        try:
            from .utils import test_signal
        except Exception:
            from utils import test_signal
        test_signal()
    except Exception as e:
        print(f"Failed to send test signal: {e}")


