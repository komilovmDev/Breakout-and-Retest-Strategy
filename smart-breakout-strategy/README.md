Smart Breakout Strategy

Overview
This is a simple Python trading bot implementing a Breakout + Retest strategy on Binance with a 1:2 risk/reward ratio. It fetches OHLCV data, identifies breakout conditions, waits for a retest, and submits a test order with logged stop-loss and take-profit targets.

Features
- Breakout + Retest logic (long-only by default)
- 1:2 risk/reward ratio
- Uses python-binance for market data and test orders
- Simple indicators using ta and pandas
- Structured logs in logs/trades.log

IMPORTANT: Live trading is not enabled by default. The example uses Binance test orders (`create_test_order`) to avoid accidental execution. Carefully review code before enabling live trading.

Project Structure
smart-breakout-strategy/
├── README.md
├── requirements.txt
├── config/
│   └── settings.json
├── src/
│   ├── main.py
│   ├── strategy.py
│   ├── utils.py
│   └── indicators.py
└── logs/
    └── trades.log

Setup
1) Create and activate a Python 3.10+ environment.
2) Install dependencies:
   pip install -r requirements.txt
3) Fill in config/settings.json with your Binance API credentials and preferred parameters.

Run
python src/main.py

Notes
- Timeframe is taken from config (`timeframe`).
- Orders are submitted using `create_test_order` for safety.
- To enable live trading, replace the test order call with `create_order` after understanding the implications.

Telegram Test Signal
1) Set your Telegram settings in `config/settings.json`:
   {
     "telegram": {
       "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
       "channel_username": "@your_channel_name"
     }
   }
   - Add your bot to the channel and grant it permission to post.
2) Install dependencies: `pip install -r requirements.txt`
3) Send a test message (either command works):
   - python smart-breakout-strategy/src/telegram_bot.py
   - python -c "import sys; sys.path.append('smart-breakout-strategy/src'); from utils import test_signal; test_signal()"
   You should see: `📢 Telegram notification sent to @your_channel_name` and the message in your channel.


