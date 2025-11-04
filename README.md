# Smart Breakout Strategy 🤖

An automated trading bot based on the "Breakout + Retest" principle with a 1:2 risk/reward ratio.  
Optimized for BTC/USDT on Binance (Spot or Futures).

## 📋 Features
- Detects breakout and retest zones
- Places automatic orders with stop-loss & take-profit
- 1:2 risk/reward ratio
- Configurable timeframes
- Logging & performance tracking

## 🧠 Strategy
- Wait for a breakout of a key level
- Confirm retest
- Enter position in direction of breakout
- SL = 0.3–0.5%, TP = 2x SL

## ⚙️ Setup
```bash
pip install -r requirements.txt
python src/main.py
