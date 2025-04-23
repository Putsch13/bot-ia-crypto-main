from datetime import datetime
import pandas as pd
import numpy as np
import requests
import pandas_ta as ta
import xgboost as xgb
import joblib
import time
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from buzz_tracker import analyze_crypto_sentiment_google
from enrich_features import enrichir_features
from tqdm import tqdm
import ccxt

MODEL_PATH = "models/model.pkl"

FEATURE_COLUMNS = [
    'rsi','stoch_rsi','stoch_rsi_k','stoch_rsi_d','macd','macd_signal','macd_diff',
    'sma_10','sma_50','ema_20','bollinger_high','bollinger_low','bollinger_width',
    'adx','volume','volume_ema','delta_pct','variation','upper_shadow','lower_shadow',
    'cci','williams_r','roc','mom','ult_osc','atr','body_size','rsi_overbought',
    'rsi_oversold','macd_cross','variation_10min','variation_1h','variation_24h',
    'sentiment','symbol_encoded'
]


# === Chargements globaux ===
try:
    label_encoder = joblib.load("models/label_encoder.pkl")
except:
    label_encoder = None
    print("⚠️ LabelEncoder non trouvé. 'symbol' sera ignoré dans certaines fonctions.")

try:
    scaler = joblib.load("models/scaler.pkl")
except:
    scaler = None
    print("⚠️ Scaler non trouvé. Les prédictions ne seront pas normalisées.")

# === Fonctions Utilitaires ===

def encoder_symbols(df):
    if "symbol" not in df.columns:
        raise ValueError("❌ Le dataset fourni n’a pas de colonne 'symbol'.")
    le = LabelEncoder()
    df["symbol_encoded"] = le.fit_transform(df["symbol"])
    return df, le

def charger_et_predire_from_df(df):
    model = joblib.load("models/model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    df_scaled = scaler.transform(df[FEATURE_COLUMNS])
    proba = model.predict_proba(df_scaled)[:, 1]
    df["prediction"] = (proba > 0.5).astype(int)
    df["confidence"] = proba
    return df



def get_top_100_symbols():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        return [coin["symbol"].upper() + "USDT" for coin in data]
    except Exception as e:
        print(f"⛔ Erreur top 100 : {e}")
        return []

def get_binance_ohlcv(symbol, interval="1m", limit=1500):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        if isinstance(data, list):
            df = pd.DataFrame(data, columns=[
                "time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
            ])
            df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
            return df
    except Exception as e:
        print(f"Erreur OHLCV Binance {symbol} : {e}")
        return None

def generer_dataset(n_points=50):
    data = []
    symbols = get_top_100_symbols()
    print(f"📅 Génération dataset pour {len(symbols)} cryptos...")

    sentiment_google = analyze_crypto_sentiment_google(symbols)

    le = LabelEncoder()
    le.fit(symbols)
    joblib.dump(le, "models/label_encoder.pkl")

    for symbol in tqdm(symbols, desc="🔄 Traitement symboles"):
        try:
            coin = symbol.replace("USDT", "")
            df = get_binance_ohlcv(symbol, interval="1m", limit=1500)
            if df is None or df.empty:
                continue

            df_enriched = enrichir_features(df)
            if df_enriched is None or df_enriched.empty:
                continue

            if df_enriched["completeness"].mean() < 0.6:
                continue

            if df_enriched.isna().mean().mean() > 0.1:
                print(f"⛔ {symbol} trop de NaN, on skip")
                continue

            sentiment = sentiment_google.get(coin, 0.0)
            symbol_encoded = le.transform([symbol])[0]

            MAX_LIGNES = 50
            for i in range(15, min(len(df_enriched) - 1, 15 + MAX_LIGNES)):
                current = df_enriched.iloc[i]
                next_close = df_enriched.iloc[i + 1]["close"]
                target = 1 if next_close > current["close"] else 0

                row = {col: current.get(col, 0) for col in FEATURE_COLUMNS}
                row["symbol"] = symbol
                row["symbol_encoded"] = symbol_encoded
                row["sentiment"] = sentiment
                row["target"] = target
                data.append(row)

            time.sleep(0.25)

        except Exception as e:
            print(f"Erreur {symbol}: {e}")
            continue

    df = pd.DataFrame(data)
    df.to_csv("dataset_trades.csv", index=False)
    print(f"✅ Dataset généré : {len(df)} lignes")
    return df

def entrainer_model():
    df = pd.read_csv("dataset_trades.csv")
    df = df[df.notna().mean(axis=1) > 0.9]

    df_majority = df[df["target"] == 0]
    df_minority = df[df["target"] == 1]
    df_minority_upsampled = df_minority.sample(len(df_majority), replace=True, random_state=42)
    df_balanced = pd.concat([df_majority, df_minority_upsampled]).sample(frac=1, random_state=42)

    X = df_balanced[FEATURE_COLUMNS]
    y = df_balanced["target"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, "models/scaler.pkl")

    model = xgb.XGBClassifier(
        eval_metric="logloss",
        max_depth=6,
        n_estimators=250,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )

    scores = cross_val_score(model, X_scaled, y, cv=5)
    print(f"📊 Résultat cross-validation : {np.mean(scores):.4f}")

    model.fit(X_scaled, y)
    joblib.dump(model, MODEL_PATH)
    print("✅ Nouveau modèle entraîné et sauvegardé")

    with open("models/feature_columns.txt", "w") as f:
        for col in FEATURE_COLUMNS:
            f.write(f"{col}\n")

def charger_modele():
    try:
        return joblib.load(MODEL_PATH)
    except:
        print("❌ Modèle manquant")
        return None

def predict_price_movement(symbol):
    try:
        print(f"🧠 Prédiction IA pour {symbol}...")

        model = charger_modele()
        if model is None:
            print("❌ modèle non chargé")
            return "INCONNU", 0.0

        df = get_binance_ohlcv(symbol, interval="1m", limit=1500)
        if df is None or df.empty:
            print("❌ OHLCV vide")
            return "INCONNU", 0.0

        df = enrichir_features(df)
        if df is None or df.empty:
            print("❌ enrichir_features retourne vide")
            return "INCONNU", 0.0

        df["symbol"] = symbol
        if label_encoder is not None:
            try:
                df["symbol_encoded"] = label_encoder.transform([symbol])[0]
                print("🔍 Symbol OK :", symbol)
            except ValueError:
                print("❌ symbol non encodable")
                return "INCONNU", 0.0
        else:
            print("❌ pas de label_encoder")
            return "INCONNU", 0.0

        # Choisir la dernière ligne complète
        current = df[df["completeness"] == 1.0].tail(1).copy()
        if current.empty:
            print("❌ Aucun point avec completeness == 1.0")
            return "INCONNU", 0.0

        # Lire colonnes utilisées à l'entraînement
        with open("models/feature_columns.txt", "r") as f:
            feature_cols = [line.strip() for line in f.readlines()]

        # Construire la ligne de features
        row = {col: current.iloc[0][col] if col in current.columns else 0 for col in feature_cols}
        print("📦 Ligne construite :", row)

        X = pd.DataFrame([row])
        if scaler:
            X = scaler.transform(X)

        proba = model.predict_proba(X)[0][1]
        prediction = "UP" if proba >= 0.5 else "DOWN"

        print(f"✅ Prediction : {prediction} avec {round(proba, 3)}")
        return prediction, round(proba, 3)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Erreur dans predict_price_movement({symbol}) → {e}")
        return "INCONNU", 0.0


def audit_model_confidence():
    df = pd.read_csv("dataset_trades.csv")
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load("models/scaler.pkl")

    with open("models/feature_columns.txt", "r") as f:
        feature_cols = [line.strip() for line in f.readlines()]

    X = df[feature_cols]
    y = df["target"]
    X_scaled = scaler.transform(X)

    y_proba = model.predict_proba(X_scaled)[:, 1]
    y_pred = model.predict(X_scaled)

    from sklearn.metrics import log_loss
    print("🔍 Audit des prédictions IA :")
    print("➡️ Moyenne proba UP :", round(np.mean(y_proba), 4))
    print("➡️ Écart-type proba :", round(np.std(y_proba), 4))
    print("➡️ LogLoss :", round(log_loss(y, y_proba), 4))
    print("➡️ % prédits UP :", round(np.mean(y_pred == 1) * 100, 2), "%")

if __name__ == "__main__":
    generer_dataset()
