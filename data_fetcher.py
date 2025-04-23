# data_fetcher.py

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import pandas_ta as ta
from enrich_features import enrichir_features



exchange = ccxt.binance({
    'enableRateLimit': True
})

def fetch_enriched_features(symbol, limit=300):
    try:
        df = fetch_ohlcv(symbol, timeframe='5m', limit=limit)
        if df is None or df.empty:
            print(f"⚠️ {symbol} → OHLCV vide")
            return None

        print(f"📦 Enrichissement de {symbol}")

        # RSI
        df['rsi'] = df.ta.rsi(length=14)

        # Stoch RSI
        stochrsi = df.ta.stochrsi(length=14)
        if stochrsi is not None and not stochrsi.empty:
            df["stoch_rsi_k"] = stochrsi["STOCHRSIk_14_14_3_3"]
            df["stoch_rsi_d"] = stochrsi["STOCHRSId_14_14_3_3"]

        # MACD
        macd = df.ta.macd()
        if macd is not None and not macd.empty:
            df["macd"] = macd["MACD_12_26_9"]
            df["macd_signal"] = macd["MACDs_12_26_9"]
            df["macd_diff"] = macd["MACDh_12_26_9"]
            df["macd_cross"] = (df["macd"] > df["macd_signal"]).astype(int)

        # Moyennes mobiles
        df["sma_10"] = df.ta.sma(length=10)
        df["sma_50"] = df.ta.sma(length=50)
        df["ema_20"] = df.ta.ema(length=20)

        # Bollinger Bands
        bb = df.ta.bbands(length=20)
        if bb is not None and not bb.empty:
            df["bollinger_high"] = bb["BBU_20_2.0"]
            df["bollinger_low"] = bb["BBL_20_2.0"]
            df["bollinger_width"] = df["bollinger_high"] - df["bollinger_low"]

        # Autres indicateurs
        df["adx"] = df.ta.adx()["ADX_14"]
        df["cci"] = df.ta.cci()
        df["roc"] = df.ta.roc()
        df["mom"] = df.ta.mom()
        df["ult_osc"] = df.ta.uo()
        df["atr"] = df.ta.atr()

        # Personnalisés
        df["delta_pct"] = df["close"].pct_change()
        df["variation"] = (df["close"] - df["open"]) / df["open"]
        df["upper_shadow"] = df["high"] - df[["close", "open"]].max(axis=1)
        df["lower_shadow"] = df[["close", "open"]].min(axis=1) - df["low"]
        df["body_size"] = abs(df["close"] - df["open"])

        df["rsi_overbought"] = (df["rsi"] > 70).astype(int)
        df["rsi_oversold"] = (df["rsi"] < 30).astype(int)

        df["variation_10min"] = df["close"].pct_change(2)  # 2*5min = 10min
        df["variation_1h"] = df["close"].pct_change(12)   # 12*5min = 1h
        df["variation_24h"] = df["close"].pct_change(288) # 288*5min = 24h

        df["sentiment"] = np.random.uniform(0, 1, len(df))  # fake pour l'instant

        # volume EMA
        df["volume_ema"] = df["volume"].ewm(span=20).mean()

        # Williams %R
        williams = df.ta.willr(length=14)
        if williams is not None:
            df["williams_r"] = williams

        # Pour stoch_rsi, tu peux utiliser le `stochrsi` complet si dispo :
        # df.ta.stochrsi(length=14, append=True) ← tu l’as sûrement déjà fait !

        df_final = df.dropna()
        if df_final.empty:
            print(f"⚠️ {symbol} → Toutes les lignes sont NaN après enrichissement")
            return None

        return df_final

    except Exception as e:
        print(f"[fetch_enriched_features ERROR] {symbol}: {e}")
        return None


def get_prix_binance(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"[get_prix_binance ERROR] {symbol}: {e}")
        return None


def fetch_ohlcv(symbol, timeframe='1h', limit=300):
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

    # Sentiment dummy
    df['sentiment'] = np.random.uniform(-1, 1, size=len(df))
    df = df.dropna()
    if df.empty:
        return None

    last = df.iloc[-1]

    result = {
        'variation_1h': (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2],
        'variation_24h': (df['close'].iloc[-1] - df['close'].iloc[-24]) / df['close'].iloc[-24],
        'volume': last['volume'],
        'rsi': last['rsi'],
        'macd': last['macd'],
        'bollinger_high': last['bollinger_high'],
        'bollinger_low': last['bollinger_low'],
        'sma_10': last['sma_10'],
        'ma_cross': last['ma_cross'],
        'sentiment': last['sentiment']
    }

    # Encoder symbol
    try:
        df_symbols = pd.read_csv("dataset_trades.csv")
        le = LabelEncoder()
        le.fit(df_symbols["symbol"].unique())
        result["symbol_encoded"] = le.transform([symbol])[0]
    except:
        result["symbol_encoded"] = 0  # fallback

    return result

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
