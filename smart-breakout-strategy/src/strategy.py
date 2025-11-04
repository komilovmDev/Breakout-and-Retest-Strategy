from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pandas as pd

try:
    from .indicators import get_breakout_levels, is_bullish_breakout, is_retest
except ImportError:  # allow running as a script
    from indicators import get_breakout_levels, is_bullish_breakout, is_retest


@dataclass
class Signal:
    side: str  # "BUY" or "NONE"
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    meta: Dict


class BreakoutRetestStrategy:
    def __init__(self, stop_loss_percent: float, risk_reward_ratio: float, lookback: int = 20, retest_tolerance: float = 0.001):
        self.stop_loss_percent = stop_loss_percent
        self.risk_reward_ratio = risk_reward_ratio
        self.lookback = lookback
        self.retest_tolerance = retest_tolerance

    def _risk_bounds(self, entry_price: float) -> Tuple[float, float]:
        stop_loss = entry_price * (1 - self.stop_loss_percent)
        take_profit = entry_price + (entry_price - stop_loss) * self.risk_reward_ratio
        return float(stop_loss), float(take_profit)

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        if len(df) < self.lookback + 5:
            return Signal(side="NONE", entry_price=None, stop_loss=None, take_profit=None, meta={"reason": "insufficient_data"})

        breakout, breakout_level = is_bullish_breakout(df, self.lookback)
        current_price = float(df.iloc[-1]["close"])  # current latest price (may be in-progress candle)

        if breakout and is_retest(current_price, breakout_level, self.retest_tolerance):
            entry = current_price
            sl, tp = self._risk_bounds(entry)
            return Signal(
                side="BUY",
                entry_price=entry,
                stop_loss=sl,
                take_profit=tp,
                meta={
                    "breakout_level": breakout_level,
                    "lookback": self.lookback,
                    "retest_tolerance": self.retest_tolerance,
                },
            )

        return Signal(side="NONE", entry_price=None, stop_loss=None, take_profit=None, meta={"breakout": breakout, "breakout_level": breakout_level})


