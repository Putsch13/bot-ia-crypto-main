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
import ta
import pandas_ta as pta  # pour les méthodes df.ta.*
import ta as ta_lib       # pour les classes comme ema_indicator, RSI, etc.

def enrichir_features(df):
    print("➡️ Colonnes AVANT enrichissement :", df.columns.tolist())
    df = df.copy()

    # Moyennes mobiles
    df['sma_10'] = df['close'].rolling(10).mean()
    df['sma_50'] = df['close'].rolling(50).mean()
    df['ema_20'] = ta_lib.trend.EMAIndicator(df['close'], window=20).ema_indicator()

    # RSI & Stoch RSI
    df['rsi'] = ta_lib.momentum.RSIIndicator(df['close'], window=14).rsi()
    stoch_rsi = ta_lib.momentum.StochRSIIndicator(df['close'], window=14)
    df['stoch_rsi'] = stoch_rsi.stochrsi()
    df['stoch_rsi_k'] = stoch_rsi.stochrsi_k()
    df['stoch_rsi_d'] = stoch_rsi.stochrsi_d()

    # MACD
    macd = ta_lib.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()

    # Bollinger Bands
    boll = ta_lib.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bollinger_high'] = boll.bollinger_hband()
    df['bollinger_low'] = boll.bollinger_lband()
    df['bollinger_width'] = boll.bollinger_wband()

    # ADX
    adx = ta_lib.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx.adx()

    # Volume, variation, shadows
    df['volume_ema'] = df['volume'].ewm(span=10).mean()
    df['delta_pct'] = df['close'].pct_change() * 100
    df['variation'] = df['close'] - df['open']
    df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
    df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']

    # Sentiment placeholder
    df['sentiment'] = 0.0

    # Variations temporelles
    df["variation_10min"] = df["close"].pct_change(periods=10) * 100
    df["variation_1h"] = df["close"].pct_change(periods=60) * 100
    df["variation_24h"] = df["close"].pct_change(periods=1440) * 100

    # Ajoute une colonne 'completeness'
    df["completeness"] = df[[
        'sma_10', 'sma_50', 'ema_20',
        'rsi', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d',
        'macd', 'macd_signal', 'macd_diff',
        'bollinger_high', 'bollinger_low', 'bollinger_width',
        'adx', 'volume_ema', 'delta_pct', 'variation',
        'upper_shadow', 'lower_shadow',
        'variation_10min', 'variation_1h', 'variation_24h'
    ]].notna().mean(axis=1)

    # Vérifie que les colonnes indispensables sont présentes
    required = ['rsi', 'macd', 'bollinger_high', 'variation']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"⛔ Colonnes manquantes dans enrichir_features: {missing}")

    print("✅ Colonnes APRÈS enrichissement :", df.columns.tolist())
    print(f"✅ {len(df)} lignes avec potentiellement des valeurs partielles.")
    return df



def analyse_technique(symbol, timeframe="1h", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": timeframe, "limit": limit}
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
    'rsi', 'stoch_rsi', 'stoch_rsi_k', 'stoch_rsi_d',
    'macd', 'macd_signal', 'macd_diff',
    'sma_10', 'sma_50', 'ema_20',
    'bollinger_high', 'bollinger_low', 'bollinger_width',
    'adx', 'volume', 'volume_ema',
    'delta_pct', 'variation',
    'upper_shadow', 'lower_shadow',
    'sentiment', 'symbol_encoded'
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
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    features = df[FEATURE_COLUMNS]

    if scaler:
        features = scaler.transform(features)

    df["prediction"] = model.predict(features)
    return df[df["prediction"] == 1]

def charger_et_predire(symbol, vars, model):
    try:
        symbol_encoded = label_encoder.transform([symbol])[0]
        data = pd.DataFrame([{
            key: vars.get(key, 0) for key in FEATURE_COLUMNS
        }])
        data["symbol_encoded"] = symbol_encoded

        if scaler:
            data = scaler.transform(data)

        return model.predict(data)[0]

    except ValueError:
        print(f"[SKIP] {symbol} ignoré (label non vu par l'IA)")
        return 0
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

    for symbol in symbols:
        try:
            coin = symbol.replace("USDT", "")
            df = get_binance_ohlcv(symbol, interval="1m", limit=1500)

            if df is None or df.empty:
                print(f"⛔ {symbol} ignoré : OHLCV vide")
                continue

            df_enriched = enrichir_features(df)

            if df_enriched is None or df_enriched.empty:
                print(f"⛔ {symbol} ignoré : enrichissement vide")
                continue

            completeness_mean = df_enriched["completeness"].mean()
            print(f"ℹ️ {symbol} → complétude moyenne : {completeness_mean:.2%}")

            if completeness_mean < 0.6:
                print(f"⚠️ {symbol} ignoré : complétude trop faible (<60%)")
                continue

            sentiment = sentiment_google.get(coin, 0.5)
            if sentiment == 0.5:
                print(f"[⚠️ SENTIMENT DEFAULT] {coin}")

            symbol_encoded = le.transform([symbol])[0]

            for i in range(15, len(df_enriched) - 1):
                current = df_enriched.iloc[i]
                next_close = df_enriched.iloc[i + 1]["close"]
                target = 1 if next_close > current["close"] else 0

                try:
                    row = {col: current[col] for col in FEATURE_COLUMNS[:-1]}
                    row["symbol"] = symbol
                    row["symbol_encoded"] = symbol_encoded
                    row["completeness"] = current["completeness"]
                    row["target"] = target
                    data.append(row)
                except KeyError as e:
                    print(f"[SKIP] {symbol} ligne {i} : feature manquante → {e}")
                    continue

        except Exception as e:
            print(f"⚠️ Erreur traitement {symbol} : {e}")
            continue

    if len(data) == 0:
        print("❌ Aucune donnée générée.")
        return pd.DataFrame()

    df_final = pd.DataFrame(data)
    df_final.to_csv("dataset_trades.csv", index=False)
    print(f"✅ Dataset généré avec succès : {len(df_final)} lignes.")
    return df_final


def entrainer_model():
    try:
        df = pd.read_csv("dataset_trades.csv")
    except pd.errors.EmptyDataError:
        print("❌ Le fichier dataset_trades.csv est vide.")
        return
    except FileNotFoundError:
        print("❌ Fichier dataset_trades.csv introuvable.")
        return

    threshold = 0.9
    df = df[df.notna().mean(axis=1) > threshold]

    if df.empty:
        print("❌ Dataset vide après suppression des NaNs.")
        return

    X = df[FEATURE_COLUMNS]
    y = df["target"]

    scaler_local = StandardScaler()
    X_scaled = scaler_local.fit_transform(X)
    joblib.dump(scaler_local, "models/scaler.pkl")

    model = xgb.XGBClassifier(
        use_label_encoder=False,
        eval_metric="logloss",
        max_depth=5,
        n_estimators=150,
        learning_rate=0.1
    )

    scores = cross_val_score(model, X_scaled, y, cv=5)
    print(f"📊 Résultat cross-validation : {np.mean(scores):.4f}")

    model.fit(X_scaled, y)
    joblib.dump(model, MODEL_PATH)

    print("✅ Modèle entraîné et sauvegardé avec succès.")

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
