from datetime import datetime
import pandas as pd
import numpy as np
import requests
import pandas_ta as ta
import xgboost as xgb
import joblib
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from buzz_tracker import analyze_crypto_sentiment_google


def analyse_technique(symbol, timeframe="1h", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": timeframe,
            "limit": limit
        }
        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        if not isinstance(data, list) or len(data) < 30:
            print(f"⛔ Pas assez de données pour {symbol}")
            return None

        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})

        # Appliquer indicateurs
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.sma(length=10, append=True)

        df.dropna(inplace=True)

        last = df.iloc[-1]

        return {
            "rsi": last["RSI_14"],
            "macd": last["MACD_12_26_9"],
            "macd_signal": last["MACDs_12_26_9"],
            "bollinger_high": last["BBU_20_2.0"],
            "bollinger_low": last["BBL_20_2.0"],
            "sma_10": last["SMA_10"],
            "volume": last["volume"],
            "variation": (last["close"] - last["open"]) / last["open"] * 100
        }

    except Exception as e:
        print(f"❌ Erreur analyse technique pour {symbol} : {e}")
        return None

MODEL_PATH = "models/model.pkl"

FEATURE_COLUMNS = [
    "rsi", "macd", "macd_signal", "sma_10",
    "bollinger_high", "bollinger_low",
    "volume", "sentiment", "variation",
    "symbol_encoded"
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

# === FONCTIONS ===

def encoder_symbols(df):
    if "symbol" not in df.columns:
        raise ValueError("❌ Le dataset fourni n’a pas de colonne 'symbol'.")
    le = LabelEncoder()
    df["symbol_encoded"] = le.fit_transform(df["symbol"])
    return df, le

def charger_et_predire_from_df(df):
    if "symbol_encoded" not in df.columns:
        raise ValueError("❌ Dataset non encodé : utilisez encoder_symbols(df) avant.")

    model = joblib.load("models/model.pkl")
    features = df[FEATURE_COLUMNS]

    if scaler:
        features = scaler.transform(features)

    df["prediction"] = model.predict(features)
    return df[df["prediction"] == 1]

def charger_et_predire(symbol, vars, model):
    try:
        symbol_encoded = label_encoder.transform([symbol])[0] if label_encoder else 0

        data = pd.DataFrame([{
            key: vars.get(key, 0) for key in FEATURE_COLUMNS
        }])
        data["symbol_encoded"] = symbol_encoded

        if scaler:
            data = scaler.transform(data)

        return model.predict(data)[0]

    except KeyError as e:
        print(f"[MISSING] Clé manquante pour {symbol} → {e}")
        return 0
    except Exception as e:
        print(f"[ERROR] Prédiction IA pour {symbol} : {e}")
        return 0

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

def get_binance_ohlcv(symbol, limit=100):
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1h", "limit": limit}
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
    print(f"📅 Dataset pour {len(symbols)} cryptos...")

    sentiment_google = analyze_crypto_sentiment_google(symbols)

    for symbol in symbols:
        try:
            coin = symbol.replace("USDT", "")
            df = get_binance_ohlcv(symbol, limit=max(n_points + 50, 100))

            if df is None or df.empty:
                print(f"⛔ {symbol} ignoré : OHLCV vide")
                continue

            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.sma(length=10, append=True)
            df.dropna(inplace=True)

            if len(df) <= 16:
                print(f"⛔ {symbol} ignoré : dataset trop court ({len(df)} lignes après indicateurs)")
                continue

            if "BBU_20_2.0" not in df.columns or "BBL_20_2.0" not in df.columns:
                print(f"⛔ {symbol} ignoré : indicateurs Bollinger manquants")
                continue

            sentiment = sentiment_google.get(coin, 0.5)
            if sentiment == 0.5:
                print(f"[⚠️ SENTIMENT DEFAULT] {coin}")

            for i in range(15, len(df) - 1):
                current = df.iloc[i]
                next_close = df.iloc[i + 1]["close"]
                target = 1 if next_close > current["close"] else 0

                if current["volume"] == 0:
                    continue

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

    if len(data) == 0:
        print("❌ Aucune donnée n’a pu être ajoutée au dataset.")
        return pd.DataFrame()

    df_final = pd.DataFrame(data)
    df_final.to_csv("dataset_trades.csv", index=False)
    print(f"✅ Dataset généré : {len(df_final)} lignes.")
    return df_final

def entrainer_model():
    try:
        df = pd.read_csv("dataset_trades.csv")
    except pd.errors.EmptyDataError:
        print("❌ Le fichier dataset_trades.csv est vide.")
        return

    df.dropna(inplace=True)

    df, le = encoder_symbols(df)
    joblib.dump(le, "models/label_encoder.pkl")

    X = df[FEATURE_COLUMNS]
    y = df["target"]

    scaler_local = StandardScaler()
    X_scaled = scaler_local.fit_transform(X)
    joblib.dump(scaler_local, "models/scaler.pkl")

    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    scores = cross_val_score(model, X_scaled, y, cv=5)
    print(f"📊 Cross-val : {np.mean(scores):.2f}")

    model.fit(X_scaled, y)
    joblib.dump(model, MODEL_PATH)
    print("✅ Modèle et scaler sauvegardés.")

def charger_modele():
    try:
        return joblib.load(MODEL_PATH)
    except:
        print("❌ Modèle manquant")
        return None

def charger_dataset_top100():
    try:
        df = pd.read_csv("dataset_trades.csv")
        if "symbol" not in df.columns:
            raise ValueError("❌ Fichier dataset_trades.csv mal formé : colonne 'symbol' manquante.")
        return df
    except pd.errors.EmptyDataError:
        print("❌ Le fichier dataset_trades.csv est vide.")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Erreur chargement dataset_top100 : {e}")
        return pd.DataFrame()

def get_trending_coins():
    try:
        return get_top_100_symbols()[:50]
    except Exception as e:
        print(f"Erreur get_trending_coins : {e}")
        return []
