# data_fetcher.py

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt

exchange = ccxt.binance({
    'enableRateLimit': True
})

def fetch_ohlcv(symbol, timeframe='1h', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"[fetch_ohlcv ERROR] {symbol}: {e}")
        return None


def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df):
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    return macd

def calculate_bollinger_bands(df, period=20):
    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return upper, lower

def fetch_real_data(symbol):
    df = fetch_ohlcv(symbol)
    if df is None or df.empty:
        return None

    df['rsi'] = calculate_rsi(df)
    df['macd'] = calculate_macd(df)
    df['bollinger_high'], df['bollinger_low'] = calculate_bollinger_bands(df)
    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['ma_cross'] = np.where(df['sma_10'] > df['close'], 1, 0)

    # Sentiment dummy (à remplacer plus tard par get_google_sentiment_score)
    df['sentiment'] = np.random.uniform(-1, 1, size=len(df))

    # Dernière ligne comme snapshot
    last = df.dropna().iloc[-1]

    return {
        'variation_1h': (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2],
        'variation_24h': (df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24],
        'volume': df['volume'].iloc[-1],
        'rsi': last['rsi'],
        'macd': last['macd'],
        'bollinger_high': last['bollinger_high'],
        'bollinger_low': last['bollinger_low'],
        'sma_10': last['sma_10'],
        'ma_cross': last['ma_cross'],
        'sentiment': last['sentiment']
    }
