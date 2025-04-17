import ccxt
import pandas as pd
import pandas_ta as ta
import os
from concurrent.futures import ThreadPoolExecutor

# Dossier de stockage des fichiers
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)

# Initialiser Binance
exchange = ccxt.binance()
exchange.load_markets()

def get_top_100_pairs():
    markets = exchange.fetch_tickers()
    usdt_pairs = [(symbol, data['quoteVolume']) for symbol, data in markets.items()
                  if symbol.endswith('/USDT') and not symbol.startswith('1000')]
    sorted_pairs = sorted(usdt_pairs, key=lambda x: x[1], reverse=True)
    return [pair[0] for pair in sorted_pairs[:100]]

def fetch_and_save(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='10m', limit=4320)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        df['rsi'] = ta.rsi(df['close'])
        macd = ta.macd(df['close'])
        df = pd.concat([df, macd], axis=1)
        df['ema20'] = ta.ema(df['close'], length=20)
        df['ema50'] = ta.ema(df['close'], length=50)

        df.dropna(inplace=True)

        filename = f"{symbol.replace('/', '')}.csv"
        df.to_csv(os.path.join(data_dir, filename))
        print(f"[✅] {symbol} saved.")
    except Exception as e:
        print(f"[❌] {symbol} failed → {e}")

if __name__ == "__main__":
    top_100 = get_top_100_pairs()
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(fetch_and_save, top_100)
