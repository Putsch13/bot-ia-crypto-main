import requests
import time
import pandas as pd
from datetime import datetime
from functools import lru_cache
import logging
from ml_brain import (
    enrichir_features,
    charger_dataset_top100,
    encoder_symbols,
    charger_et_predire_from_df,
    charger_modele
)
from buzz_tracker import analyze_crypto_sentiment_google
import requests
from requests.exceptions import RequestException

def safe_check_symbol_on_binance(symbol, retries=2, timeout=5):
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        for _ in range(retries):
            try:
                res = requests.get(url, timeout=timeout)
                res.raise_for_status()
                data = res.json()
                available_symbols = {s["symbol"] for s in data["symbols"]}
                return symbol in available_symbols
            except RequestException as e:
                continue  # Réessaye
    except Exception as final_e:
        logger.error(f"[BINANCE] ❌ Erreur finale pour {symbol} : {final_e}")
    return False

# === LOGGER CONFIG ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# === CONFIGS ===
BINANCE_API_BASE = "https://api.binance.com"
BINANCE_TICKER_URL = f"{BINANCE_API_BASE}/api/v3/ticker/24hr"
BINANCE_KLINES_URL = f"{BINANCE_API_BASE}/api/v3/klines"

WEIGHT_VARIATION = 0.4
WEIGHT_SENTIMENT = 0.3
WEIGHT_PREDICTION = 0.3

latest_ia_report = None
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

@lru_cache(maxsize=3)
def get_top_100_symbols():
    logger.info("🔀 Récupération des 100 cryptos les plus actives sur Binance...")
    try:
        res = requests.get(BINANCE_TICKER_URL, timeout=10)
        data = res.json()
        usdt_pairs = [d for d in data if d['symbol'].endswith("USDT")]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        symbols = [coin["symbol"] for coin in sorted_pairs[:100]]
        logger.info(f"✅ {len(symbols)} cryptos récupérées depuis Binance.")
        return symbols
    except Exception as e:
        logger.error(f"⛔ Erreur Binance API : {e}")
        return []

def is_symbol_valid_on_binance(symbol):
    try:
        url = f"{BINANCE_API_BASE}/api/v3/exchangeInfo"
        res = requests.get(url, timeout=10)
        data = res.json()
        available_symbols = {s["symbol"] for s in data["symbols"]}
        return symbol in available_symbols
    except Exception as e:
        logger.error(f"Erreur vérification Binance pour {symbol}: {e}")
        return False

def get_price(symbol: str, minutes_ago: int):
    try:
        interval = "1h" if minutes_ago > 1000 else "1m"
        limit = (minutes_ago // 60 + 1) if interval == "1h" else minutes_ago + 1
        url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=10)
        data = res.json()

        if isinstance(data, list) and len(data) > 0:
            index = -(minutes_ago // (60 if interval == "1h" else 1) + 1)
            return float(data[index][4])
    except Exception as e:
        logger.error(f"⚠️ Erreur get_price({symbol}, {minutes_ago} min): {e}")
    return None

def get_variations(symbol):
    logger.info(f"🔀 Récupération des variations pour {symbol}...")
    now = get_price(symbol, 0)
    if now is None:
        return None
    intervals = {"variation_10min": 10, "variation_1h": 60, "variation_24h": 1440}
    variations = {}
    for label, minutes in intervals.items():
        past = get_price(symbol, minutes)
        if past and past > 0:
            variations[label] = round((now - past) / past * 100, 2)
        else:
            variations[label] = None
            logger.warning(f"{label} est None pour {symbol}")
    return variations

def get_sentiment_scores_dynamic(symbols):
    logger.info("Récupération des scores de sentiment Google...")
    coins = [s.replace("USDT", "") for s in symbols]
    g_scores = analyze_crypto_sentiment_google(coins)
    return {coin.upper(): {"google": g, "total": g} for coin, g in g_scores.items()}

def get_ohlcv_df(symbol: str):
    try:
        url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval=1m&limit=2000"
        res = requests.get(url, timeout=10)
        data = res.json()

        if not isinstance(data, list) or len(data) == 0:
            logger.warning(f"⚠️ Données OHLCV invalides pour {symbol}")
            return None

        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "_1", "_2", "_3", "_4", "_5", "_6"
        ])

        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        df.set_index("timestamp", inplace=True)
        df = df.sort_index()
        logger.info(f"➡️ {symbol} → {len(df)} lignes OHLCV récupérées (interval=1m)")
        return df

    except Exception as e:
        logger.error(f"⛔ Erreur get_ohlcv_df({symbol}): {e}")
        return None

def run_full_audit():
    global latest_ia_report
    logger.info("🧐 Lancement de l'audit complet IA...")
    start_time = time.time()

    model = charger_modele()
    if not model:
        logger.error("❌ Modèle non chargé.")
        return

    symbols = get_top_100_symbols()
    logger.info(f"🔢 {len(symbols)} cryptos à analyser.")

    sentiments = get_sentiment_scores_dynamic(symbols)
    rows, explanations, errors = [], [], []

    for symbol in symbols:
        if not safe_check_symbol_on_binance(symbol):
            logger.warning(f"❌ {symbol} non reconnu sur Binance, skip.")
            continue
        time.sleep(0.25)  # ⏱️ Laisse souffler Binance

        logger.info(f"🔍 Analyse IA pour {symbol}...")

        try:
            df = get_ohlcv_df(symbol)
            if df is None or df.empty:
                logger.warning(f"⚠️ Données OHLCV vides pour {symbol}, skip.")
                continue

            df = enrichir_features(df)
            if df is None or df.empty:
                logger.warning(f"⚠️ Données enrichies vides pour {symbol}, skip.")
                continue

            df["symbol"] = symbol

            df, _ = encoder_symbols(df)
            if "symbol_encoded" not in df.columns:
                raise ValueError("❌ symbol_encoded manquant après encodage")

            coin = symbol.replace("USDT", "")
            sentiment = sentiments.get(coin, {}).get("total", 0.5)
            df["sentiment"] = sentiment

            df["completeness"] = df[FEATURE_COLUMNS].notna().mean(axis=1)
            missing_cols = [col for col in FEATURE_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"❌ Colonnes manquantes : {missing_cols}")

            pred_score = charger_et_predire_from_df(df)

            # Gestion robuste du format de prédiction
            if isinstance(pred_score, pd.DataFrame) and "prediction" in pred_score.columns:
                pred = pred_score["prediction"].iloc[-1]
            elif isinstance(pred_score, (int, float)):
                pred = pred_score
            else:
                logger.warning(f"[{symbol}] Format inattendu pour pred_score: {type(pred_score)}")
                pred = 0

            # Vérification finale anti-NaN
            try:
                pred = float(pred)
                if pd.isna(pred):
                    pred = 0
            except Exception:
                pred = 0

            latest = df.iloc[-1]
            narration = [
                f"Variation 10min: {latest['variation_10min']:.2f}%",
                f"RSI: {latest['rsi']:.2f}",
                f"MACD: {latest['macd']:.2f}",
                f"Sentiment Google: {sentiment * 100:.1f}%",
                f"IA: {'Hausse' if pred == 1 else 'Baisse'}"
            ]

            # 🔐 Anti-NaN fallback pour les variations
            v10 = latest["variation_10min"]
            v1h = latest["variation_1h"]
            v24h = latest["variation_24h"]

            # Utiliser 0.0 comme fallback si valeur NaN
            v10 = v10 if pd.notna(v10) else 0.0
            v1h = v1h if pd.notna(v1h) else 0.0
            v24h = v24h if pd.notna(v24h) else 0.0
            sent = sentiment if pd.notna(sentiment) else 0.5
            

            # Score de variation pondéré
            score_variation = v10 * 0.2 + v1h * 0.4 + v24h * 0.4

            # Log debug pour comprendre les valeurs utilisées
            logger.debug(f"[{symbol}] var10={v10} var1h={v1h} var24h={v24h} sentiment={sent} pred={pred} completeness={latest['completeness']}")

            score_ia = round((
                WEIGHT_VARIATION * score_variation +
                WEIGHT_SENTIMENT * sent * 100 +
                WEIGHT_PREDICTION * pred * 100
            ) * latest["completeness"], 2)

            logger.info(f"✅ {symbol} audité avec score IA {score_ia}")

            rows.append({
                "symbol": symbol,
                "sentiment": sentiment,
                "score_ia": score_ia,
                "variation_10min": latest["variation_10min"],
                "variation_1h": latest["variation_1h"],
                "variation_24h": latest["variation_24h"]
            })

            explanations.append({
                "crypto": symbol,
                "explanation": " | ".join(narration)
            })

        except Exception as e:
            logger.error(f"❌ Échec analyse pour {symbol} : {e}")
            errors.append(f"{symbol} → {e}")
            continue

        time.sleep(0.2)

    if not rows:
        logger.warning("⚠️ Aucun résultat à auditer, DataFrame vide.")
        return [], [], "❌ Aucun crypto n'a pu être audité avec succès."

    if errors:
        logger.warning("🧨 Résumé des erreurs d'audit :")
        for err in errors:
            logger.warning(f"  ⛔ {err}")
    

    logger.info(f"✅ Audit terminé. {len(rows)} cryptos analysées.")
    df = pd.DataFrame(rows).sort_values("score_ia", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df["datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filename = f"audit_100cryptos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)

    top5 = df.head(5).to_dict("records")
    flop5 = df.tail(5).to_dict("records")

    rapport = "\n\n✅ Audit IA - Rapport Complet\n\n"
    rapport += "----- Top 5 Cryptos Recommandées -----\n"
    for c in top5:
        exp = next((e['explanation'] for e in explanations if e['crypto'] == c['symbol']), "Pas d'explication.")
        rapport += f"→ {c['symbol']} (Score IA: {c['score_ia']})\n   {exp}\n\n"

    rapport += "----- Flop 5 Cryptos à Éviter -----\n"
    for c in flop5:
        exp = next((e['explanation'] for e in explanations if e['crypto'] == c['symbol']), "Pas d'explication.")
        rapport += f"→ {c['symbol']} (Score IA: {c['score_ia']})\n   {exp}\n\n"

    if errors:
        rapport += "----- Erreurs rencontrées -----\n"
        for err in errors:
            rapport += f"{err}\n"

    duration = int(time.time() - start_time)
    latest_ia_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "top": top5,
        "flop": flop5,
        "rapport": rapport,
        "duration": duration
    }

    logger.info(f"✅ Rapport IA généré avec succès en {duration}s.")
    return top5, flop5, rapport

if __name__ == "__main__":
    top5, flop5, rapport = run_full_audit()
    print(rapport)
