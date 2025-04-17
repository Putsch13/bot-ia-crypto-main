import pandas as pd
import numpy as np
import requests
import pandas_ta as ta
from buzz_tracker import analyze_crypto_sentiment_google, analyze_crypto_sentiment_twitter
from data_fetcher import get_binance_ohlcv

# === Génération du dataset complet ===

def generer_dataset(n_points=50):
    data = []
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        coins = res.json()
        symbols = [coin["symbol"].upper() + "USDT" for coin in coins]
    except Exception as e:
        print(f"⛔ Erreur récupération top 100 : {e}")
        return pd.DataFrame()

    print(f"📅 Génération dataset IA pour {len(symbols)} cryptos...")

    sentiment_google = analyze_crypto_sentiment_google(symbols)
    sentiment_twitter = analyze_crypto_sentiment_twitter(symbols)

    for symbol in symbols:
        coin = symbol.replace("USDT", "")
        try:
            df = get_binance_ohlcv(symbol, n_points + 50)
            if df is None or df.empty or len(df) < n_points:
                continue

            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.bbands(append=True)
            df.ta.sma(length=10, append=True)

            sentiment = (sentiment_google.get(coin, 0.5) + sentiment_twitter.get(coin, 0.5)) / 2

            for i in range(15, len(df) - 1):
                current = df.iloc[i]
                next_close = df.iloc[i + 1]["close"]
                target = 1 if next_close > current["close"] else 0

                row = {
                    "symbol": symbol,
                    "rsi": current["RSI_14"],
                    "macd": current["MACD_12_26_9"],
                    "macd_signal": current["MACDs_12_26_9"],
                    "bollinger_high": current["BBU_20_2.0"],
                    "bollinger_low": current["BBL_20_2.0"],
                    "sma_10": current["SMA_10"],
                    "volume": current["volume"],
                    "sentiment": sentiment,
                    "variation": (current["close"] - current["open"]) / current["open"] * 100,
                    "target": target
                }

                data.append(row)

        except Exception as e:
            print(f"⚠️ Erreur {symbol} : {e}")

    df_final = pd.DataFrame(data)
    df_final.dropna(inplace=True)
    df_final.to_csv("dataset_trades.csv", index=False)
    print(f"✅ Dataset généré : {len(df_final)} lignes.")
    return df_final
