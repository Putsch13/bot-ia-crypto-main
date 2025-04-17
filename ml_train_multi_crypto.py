
import ccxt
import pandas as pd
import numpy as np
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
from buzz_tracker import analyze_crypto_sentiment
from twitter_tracker import analyze_crypto_sentiment_twitter

exchange = ccxt.binance()
exchange.enableRateLimit = True

import ccxt

def get_top_cryptos(limit=100):
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    
    usdt_pairs = [symbol for symbol in markets if symbol.endswith("/USDT")]
    # Optional : trier par volume ou un autre critère
    return usdt_pairs[:limit]

cryptos = get_top_cryptos(limit=100)


def get_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["ma20"] = df["close"].rolling(20).mean()
    df["ma50"] = df["close"].rolling(50).mean()
    df["rsi"] = compute_rsi(df["close"], 14)
    df["ma_cross"] = (df["ma20"] > df["ma50"]).astype(int)
    df["future_close"] = df["close"].shift(-1)
    df["target"] = (df["future_close"] > df["close"]).astype(int)
    df = df.dropna()
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def train_model():
    all_data = []
    google_scores = analyze_crypto_sentiment()
    twitter_scores = analyze_crypto_sentiment_twitter()

    for symbol in cryptos:
        try:
            df = get_data(symbol)
            coin = symbol.split("/")[0]
            df["sentiment_score_google"] = google_scores.get(coin, 0)
            df["sentiment_score_twitter"] = twitter_scores.get(coin, 0)
            df["sentiment_score_total"] = df["sentiment_score_google"] + df["sentiment_score_twitter"]
            all_data.append(df)
            print(f"✅ Données récupérées pour {symbol}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Erreur avec {symbol}: {e}")
            continue

    dataset = pd.concat(all_data)
    X = dataset[["rsi", "volume", "ma_cross", "sentiment_score_total"]]
    y = dataset["target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Accuracy du modèle : {acc:.2f}")

    joblib.dump(model, "model_bot.pkl")
    print("🧠 Modèle sauvegardé dans model_bot.pkl")

if __name__ == "__main__":
    train_model()
