import requests
import time
import pandas as pd
from datetime import datetime
from functools import lru_cache
import logging
from ml_brain import charger_dataset_top100, encoder_symbols, charger_et_predire_from_df

df = charger_dataset_top100()
df, _ = encoder_symbols(df)
top_cryptos = charger_et_predire_from_df(df)

# === IMPORTS INTERNES ===
from ml_brain import charger_modele, charger_et_predire
from buzz_tracker import analyze_crypto_sentiment_google




# === LOGGER CONFIG ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
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

@lru_cache(maxsize=3)
def get_top_100_symbols():
    logger.info("🔄 Récupération des 100 cryptos les plus actives sur Binance...")
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
        url = f"{BINANCE_KLINES_URL}?symbol={symbol}&interval=1m&limit={minutes_ago + 1}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if isinstance(data, list) and len(data) > minutes_ago:
            return float(data[-(minutes_ago + 1)][4])
    except Exception as e:
        logger.error(f"⚠️ Erreur get_price({symbol}, {minutes_ago} min): {e}")
    return None

def get_variations(symbol):
    logger.info(f"🔄 Récupération des variations pour {symbol}...")
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
    return variations

def get_sentiment_scores_dynamic(symbols):
    logger.info("Récupération des scores de sentiment Google...")
    coins = [s.replace("USDT", "") for s in symbols]
    g_scores = analyze_crypto_sentiment_google(coins)
    
    result = {}
    for coin in g_scores.keys():
        g = g_scores.get(coin, 0.5)
        result[coin.upper()] = {"google": g, "total": g}
    return result

def run_full_audit():
    global latest_ia_report
    logger.info("🧠 Lancement run_full_audit()")
    start_time = time.time()

    model = charger_modele()
    if not model:
        logger.error("❌ Modèle non chargé.")
        return

    symbols = get_top_100_symbols()
    logger.info(f"🔢 {len(symbols)} cryptos à analyser (via get_top_100_symbols())")
    sentiments = get_sentiment_scores_dynamic(symbols)
    rows, explanations = [], []

    for symbol in symbols:
        if not is_symbol_valid_on_binance(symbol):
            continue

        variations = get_variations(symbol)
        if not variations:
            continue

        coin = symbol.replace("USDT", "")
        sentiment = sentiments.get(coin, {"total": 0})["total"]
        pred_score = 0
        narration = []

        try:
            pred_score = charger_et_predire(symbol, variations, model)
            narration.append("Prédiction IA: " + ("Hausse" if pred_score == 1 else "Baisse"))
        except Exception as e:
            logger.error(f"❌ Erreur de prédiction pour {symbol}: {e}")
            narration.append("Prédiction IA: Indisponible")

        if variations["variation_10min"] is not None:
            narration.append(f"Variation sur 10 min: {variations['variation_10min']}%")
        if variations["variation_1h"] is not None:
            narration.append(f"Variation sur 1h: {variations['variation_1h']}%")
        if variations["variation_24h"] is not None:
            narration.append(f"Variation sur 24h: {variations['variation_24h']}%")
        
        narration.append(f"Sentiment global (Google): {sentiment*100:.1f}%")

        explanation_text = (
            f"La crypto {symbol} présente une variation moyenne de {variations['variation_10min']}% sur 10 minutes, "
            f"{variations['variation_1h']}% sur 1 heure, et {variations['variation_24h']}% sur 24 heures. "
            f"Le sentiment détecté via Google est de {sentiment*100:.1f}%. "
            f"L'IA prédit une {'hausse' if pred_score == 1 else 'baisse'}."
        )
        narration.append(explanation_text)

        score_variation = (
            (variations["variation_10min"] or 0) * 0.2 +
            (variations["variation_1h"] or 0) * 0.4 +
            (variations["variation_24h"] or 0) * 0.4
        )
        score_ia = round(
            WEIGHT_VARIATION * score_variation +
            WEIGHT_SENTIMENT * sentiment * 100 +
            WEIGHT_PREDICTION * pred_score * 100,
            2
        )

        rows.append({
            "symbol": symbol,
            **variations,
            "sentiment": sentiment,
            "score_ia": score_ia
        })

        explanations.append({
            "crypto": symbol,
            "explanation": " | ".join(narration)
        })

        time.sleep(0.2)

    logger.info(f"✅ Audit terminé. {len(rows)} cryptos ont été auditées avec succès.")

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
