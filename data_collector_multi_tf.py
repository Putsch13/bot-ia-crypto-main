import ccxt
import pandas as pd
import pandas_ta as ta
import os
from concurrent.futures import ThreadPoolExecutor

# Directory to save the CSVs
data_dir = "data_multi_tf"
os.makedirs(data_dir, exist_ok=True)

# Initialize Binance
exchange = ccxt.binance()
exchange.load_markets()

# Define timeframes and their corresponding limits
timeframes = {
    '1m': 1440 * 3,   # 3 days of 1m
    '3m': 1440,       # 3 days of 3m
    '5m': 864,        # 3 days of 5m
    '15m': 2880,      # 30 days
    '30m': 1440,
    '1h': 720,
    '1d': 60,
    '1w': 26
}

# Get Top 100 USDT pairs by volume
def get_top_100_pairs():
    tickers = exchange.fetch_tickers()
    usdt_pairs = [(symbol, data['quoteVolume']) for symbol, data in tickers.items()
                  if symbol.endswith('/USDT') and not symbol.startswith('1000')]
    sorted_pairs = sorted(usdt_pairs, key=lambda x: x[1], reverse=True)
    return [pair[0] for pair in sorted_pairs[:100]]

# Fetch and save data for a symbol and timeframe
def fetch_symbol_timeframe(symbol, timeframe, limit):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Add indicators
        df['rsi'] = ta.rsi(df['close'])
        macd = ta.macd(df['close'])
        df = pd.concat([df, macd], axis=1)
        df['ema20'] = ta.ema(df['close'], length=20)
        df['ema50'] = ta.ema(df['close'], length=50)

        df.dropna(inplace=True)

        filename = f"{symbol.replace('/', '')}_{timeframe}.csv"
        df.to_csv(os.path.join(data_dir, filename))
        print(f"[✅] Saved {filename}")
    except Exception as e:
        print(f"[❌] Failed {symbol} [{timeframe}] → {e}")

# Run all tasks
if __name__ == "__main__":
    tasks = []
    top_100 = get_top_100_pairs()
    for symbol in top_100:
        for tf, limit in timeframes.items():
            tasks.append((symbol, tf, limit))

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda args: fetch_symbol_timeframe(*args), tasks)
