import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from telegram import Bot


def load_settings(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_logger(log_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger("smart_breakout")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    return logger


def get_binance_client(api_key: str, api_secret: str, mode: str = "demo") -> Client:
    """Return a Binance client configured for demo (production endpoint, test orders)
    or testnet (testnet endpoint, live testnet orders).
    """
    client = Client(api_key, api_secret)
    if str(mode).lower() == "testnet":
        # Ensure spot testnet base URL is used
        try:
            client = Client(api_key, api_secret, testnet=True)
        except TypeError:
            # Fallback for client versions without testnet kwarg support
            client = Client(api_key, api_secret)
        # Explicitly set API URL in case library version doesn't auto-switch
        client.API_URL = "https://testnet.binance.vision/api"
    return client


def fetch_klines(client: Client, symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    """Fetch historical klines and return as a pandas DataFrame with proper dtypes."""
    raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    cols = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]
    df = pd.DataFrame(raw, columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = df[c].astype(float)
    return df[["open_time", "open", "high", "low", "close", "volume", "close_time"]]


def now_ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def compute_sl_tp(entry_price: float, side: str, stop_loss_percent: float, risk_reward_ratio: float) -> Tuple[float, float]:
    entry = float(entry_price)
    sl_dist = entry * float(stop_loss_percent)
    tp_dist = sl_dist * float(risk_reward_ratio)
    if str(side).upper() == SIDE_BUY:
        sl = entry - sl_dist
        tp = entry + tp_dist
    else:
        sl = entry + sl_dist
        tp = entry - tp_dist
    return float(sl), float(tp)


def place_order(
    client: Client,
    mode: str,
    symbol: str,
    side: str,
    quantity: float,
    entry_price: float,
    stop_loss_percent: float,
    risk_reward_ratio: float,
    logger: logging.Logger,
) -> None:
    """Place an order depending on mode (demo uses test order on prod endpoint; testnet places live orders on testnet).
    Prints/logs entry, SL, TP, and order type.
    """
    side_u = str(side).upper()
    if side_u not in (SIDE_BUY, SIDE_SELL):
        raise ValueError(f"Unsupported side: {side}")

    sl, tp = compute_sl_tp(entry_price, side_u, stop_loss_percent, risk_reward_ratio)
    order_type = ORDER_TYPE_MARKET

    logger.info(
        f"Placing {('TEST ' if str(mode).lower()=='demo' else '')}{order_type} {side_u} {symbol} qty={quantity} entry≈{entry_price:.6f} SL={sl:.6f} TP={tp:.6f}"
    )
    print(
        f"ORDER -> type={order_type}, side={side_u}, symbol={symbol}, qty={quantity}, entry≈{entry_price:.6f}, SL={sl:.6f}, TP={tp:.6f}"
    )

    try:
        if str(mode).lower() == "testnet":
            client.create_order(symbol=symbol, side=side_u, type=order_type, quantity=quantity)
        else:
            client.create_test_order(symbol=symbol, side=side_u, type=order_type, quantity=quantity)
        logger.info("Order submitted successfully")
    except Exception as e:
        logger.exception(f"Order submission failed: {e}")


def _normalize_channel_username(channel_username: str) -> str:
    """Normalize channel identifier to '@channelname' if a URL is provided."""
    raw = (channel_username or "").strip()
    if "t.me/" in raw:
        # extract the last segment after '/'
        segment = raw.split("t.me/")[-1].strip().strip("/")
        if not segment.startswith("@"):
            return f"@{segment}"
        return segment
    return raw


def send_telegram_message(bot_token: str, channel_username: str, text: str, logger: logging.Logger) -> None:
    if not bot_token or not channel_username:
        return
    try:
        bot = Bot(token=bot_token)
        target = _normalize_channel_username(channel_username)
        bot.send_message(chat_id=target, text=text, disable_web_page_preview=True)
        logger.info(f"Telegram message sent to {target}")
    except Exception as e:
        logger.exception(f"Failed to send Telegram message: {e}")


def test_signal() -> None:
    """Send a hardcoded test signal to Telegram using src/telegram_bot.py sender."""
    # Lazy import to avoid circular imports
    try:
        from .telegram_bot import send_telegram_message as _send
    except Exception:
        from telegram_bot import send_telegram_message as _send

    msg = (
        "🚀 Smart Breakout Strategy TEST\n"
        "Signal: BUY\n"
        "Entry: 100000\n"
        "SL: 99500\n"
        "TP: 102000\n"
        "Mode: Test"
    )
    _send(msg)

