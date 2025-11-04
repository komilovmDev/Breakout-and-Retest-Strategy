import os
import sys
from typing import Dict

from binance.client import Client
from binance.enums import SIDE_BUY

try:
    from .utils import fetch_klines, get_binance_client, init_logger, load_settings, safe_float, place_order, send_telegram_message
    from .strategy import BreakoutRetestStrategy
except ImportError:  # allow running as a script
    from utils import fetch_klines, get_binance_client, init_logger, load_settings, safe_float, place_order, send_telegram_message
    from strategy import BreakoutRetestStrategy


INTERVAL_MAP: Dict[str, str] = {
    "1m": Client.KLINE_INTERVAL_1MINUTE,
    "3m": Client.KLINE_INTERVAL_3MINUTE,
    "5m": Client.KLINE_INTERVAL_5MINUTE,
    "15m": Client.KLINE_INTERVAL_15MINUTE,
    "30m": Client.KLINE_INTERVAL_30MINUTE,
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "2h": Client.KLINE_INTERVAL_2HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
}


def main() -> None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "settings.json")
    log_path = os.path.join(base_dir, "logs", "trades.log")

    logger = init_logger(log_path)
    settings = load_settings(config_path)

    api_key = settings.get("API_KEY", "")
    api_secret = settings.get("API_SECRET", "")
    symbol = settings.get("symbol", "BTCUSDT")
    timeframe = settings.get("timeframe", "1h")
    rr = safe_float(settings.get("risk_reward_ratio", 2.0), 2.0)
    sl_pct = safe_float(settings.get("stop_loss_percent", 0.003), 0.003)
    quantity = safe_float(settings.get("quantity", 0.001), 0.001)
    mode = str(settings.get("mode", "demo")).lower()
    telegram_cfg = settings.get("telegram", {}) or {}
    bot_token = telegram_cfg.get("bot_token", "")
    channel_username = telegram_cfg.get("channel_username", "")

    interval = INTERVAL_MAP.get(timeframe)
    if not interval:
        logger.error(f"Unsupported timeframe: {timeframe}")
        sys.exit(1)

    client: Client = get_binance_client(api_key, api_secret, mode=mode)

    try:
        df = fetch_klines(client, symbol, interval, limit=300)
    except Exception as e:
        logger.exception(f"Failed to fetch klines: {e}")
        sys.exit(1)

    strategy = BreakoutRetestStrategy(stop_loss_percent=sl_pct, risk_reward_ratio=rr, lookback=20, retest_tolerance=sl_pct)
    signal = strategy.generate_signal(df)

    if signal.side == "BUY" and signal.entry_price and signal.stop_loss and signal.take_profit:
        logger.info(
            f"Signal BUY {symbol} qty={quantity} entry≈{signal.entry_price:.2f} SL={signal.stop_loss:.2f} TP={signal.take_profit:.2f}"
        )
        place_order(
            client=client,
            mode=mode,
            symbol=symbol,
            side=SIDE_BUY,
            quantity=quantity,
            entry_price=float(signal.entry_price),
            stop_loss_percent=sl_pct,
            risk_reward_ratio=rr,
            logger=logger,
        )

        # Telegram notification
        msg = (
            "🚀 Smart Breakout Strategy\n"
            f"Signal: BUY\n"
            f"Entry: {float(signal.entry_price):.2f}\n"
            f"SL: {float(signal.stop_loss):.2f}\n"
            f"TP: {float(signal.take_profit):.2f}\n"
            f"Mode: {'Testnet' if mode=='testnet' else 'Demo'}"
        )
        send_telegram_message(bot_token=bot_token, channel_username=channel_username, text=msg, logger=logger)
    else:
        logger.info(f"No actionable signal. Meta: {signal.meta}")


if __name__ == "__main__":
    main()


