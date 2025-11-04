from typing import Tuple

import pandas as pd
from ta.volatility import AverageTrueRange


def compute_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=window)
    return atr.average_true_range()


def get_breakout_levels(df: pd.DataFrame, lookback: int = 20) -> Tuple[float, float]:
    """Return (highest_high, lowest_low) over the last `lookback` candles excluding the most recent closed candle.
    Use this to detect breakouts relative to recent structure.
    """
    if len(df) < lookback + 2:
        return float("nan"), float("nan")
    window = df.iloc[-(lookback + 1) : -1]
    highest_high = window["high"].max()
    lowest_low = window["low"].min()
    return float(highest_high), float(lowest_low)


def is_bullish_breakout(df: pd.DataFrame, lookback: int = 20) -> Tuple[bool, float]:
    """True if the last closed candle closed above the highest high of previous N candles."""
    if len(df) < lookback + 2:
        return False, float("nan")
    highest_high, _ = get_breakout_levels(df, lookback)
    last_close = float(df.iloc[-2]["close"])  # last closed candle
    return last_close > highest_high, highest_high


def is_retest(current_price: float, level: float, tolerance_percent: float = 0.001) -> bool:
    if level != level:  # NaN check
        return False
    lower = level * (1 - tolerance_percent)
    upper = level * (1 + tolerance_percent)
    return lower <= float(current_price) <= upper


