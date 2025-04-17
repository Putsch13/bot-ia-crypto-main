import os
import ccxt
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from buzz_tracker import get_google_sentiment_score  # 📊 Sentiment Google News
from data_fetcher import fetch_real_data  # Si tu l’utilises ailleurs aussi
from ml_dataset_builder import generer_dataset
from sklearn.preprocessing import LabelEncoder
from ml_brain import encoder_symbols, charger_dataset_top100

df = charger_dataset_top100()
df, le = encoder_symbols(df)

# ... puis split, train, save

le = LabelEncoder()
df["symbol_encoded"] = le.fit_transform(df["symbol"])

# === Paramètres ===
EXPECTED_FEATURES = [
    'rsi', 'macd', 'macd_signal', 'bollinger_high', 'bollinger_low',
    'sma_10', 'volume', 'sentiment', 'variation'
]
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")


# === Top cryptos USDT sur Binance ===
def get_top_cryptos(limit=100):
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if s.endswith("/USDT") and ":" not in s]
    return usdt_pairs[:limit]


# === Données techniques & sentiment pour un symbole ===
def fetch_features(symbol):
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=30)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # === Indicateurs techniques ===
        variation = (df["close"].iloc[-1] - df["open"].iloc[-1]) / df["open"].iloc[-1] * 100
        macd = df["close"].ewm(span=12).mean().iloc[-1] - df["close"].ewm(span=26).mean().iloc[-1]
        macd_signal = df["close"].ewm(span=9).mean().iloc[-1]
        sma_10 = df["close"].rolling(10).mean().iloc[-1]
        std_10 = df["close"].rolling(10).std().iloc[-1]
        bollinger_high = sma_10 + 2 * std_10
        bollinger_low = sma_10 - 2 * std_10

        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=14).mean().iloc[-1]
        avg_loss = loss.rolling(window=14).mean().iloc[-1]
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        sentiment = get_google_sentiment_score(symbol.split("/")[0])
        volume = df["volume"].mean()

        return pd.DataFrame([{
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "bollinger_high": bollinger_high,
            "bollinger_low": bollinger_low,
            "sma_10": sma_10,
            "volume": volume,
            "sentiment": sentiment,
            "variation": variation,
            "target": np.random.choice([0, 1])  # placeholder à remplacer
        }])
    except Exception as e:
        print(f"[WARN] Erreur récupération pour {symbol}: {e}")
        return pd.DataFrame([{f: 0 for f in EXPECTED_FEATURES + ["target"]}])


# === Génération du dataset complet ===
def build_dataset(symbols):
    df_total = pd.DataFrame()
    for symbol in symbols:
        data = fetch_features(symbol)
        df_total = pd.concat([df_total, data], ignore_index=True)
    return df_total


# === Entraînement du modèle IA ===
def train_model():
    print("[INFO] 🔍 Récupération du top 100 crypto...")
    cryptos = get_top_cryptos(limit=100)
    print(f"[INFO] ✅ {len(cryptos)} cryptos chargées")

    df = build_dataset(cryptos)
    for col in EXPECTED_FEATURES:
        if col not in df.columns:
            df[col] = 0
    df = df[EXPECTED_FEATURES + ["target"]]

    X = df.drop(columns=["target", "symbol"])  # on garde symbol_encoded
    y = df["target"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(le, "models/label_encoder.pkl")

    print("✅ Modèle entraîné et sauvegardé dans :", MODEL_DIR)
    print("🧠 Features utilisées :", list(X.columns))
    print("📊 Feature importances :")
    for name, importance in zip(X.columns, model.feature_importances_):
        print(f"  - {name}: {importance:.4f}")


# === Exécution directe ===
if __name__ == "__main__":
    train_model()
