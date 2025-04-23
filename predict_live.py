import os
import csv
from datetime import datetime
import pandas as pd
from ml_utils import predict_price_movement


# ====== 🔧 CONFIGURATION ======
CSV_PATH = 'audit_100cryptos.csv'
HISTO_PATH = 'historique_trades.csv'
LOG_PATH = 'logs_robot.txt'
LOG_FILE = "logs/ia_predictions_log.csv"
SCORE_MIN = 30  # Score IA minimal requis pour trader

# ====== 📊 LOGGER DE PRÉDICTION ======
def log_prediction(symbol, score, proba, sentiment, var_1h, prediction=None, real=None, confidence=None, result=None):
    import os
    import csv
    from datetime import datetime

    os.makedirs("logs", exist_ok=True)
    log_path = "logs/ia_predictions_log.csv"
    file_exists = os.path.isfile(log_path)

    fieldnames = [
        "Date", "Symbol", "Score", "Probabilité", "Sentiment", "Variation_1h",
        "Prediction", "Real", "Confidence", "Result"
    ]

    with open(log_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Symbol": symbol,
            "Score": round(score, 2),
            "Probabilité": round(proba, 4),
            "Sentiment": round(sentiment, 2),
            "Variation_1h": round(var_1h, 2),
            "Prediction": prediction,
            "Real": real,
            "Confidence": round(confidence, 4) if confidence is not None else "",
            "Result": result or ""
        })


# ====== 🛒 SIMULATION DE TRADE ======
def execute_trade(symbol, mode='fictif'):
    """Exécute un trade fictif ou réel et log l'action."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action = 'BUY'
    montant_usdt = 100

    print(f"[{now}] 🛒 Exécution {mode.upper()} : {action} {symbol} pour {montant_usdt} USDT")

    trade_data = {
        'timestamp': now,
        'symbol': symbol,
        'mode': mode,
        'action': action,
        'montant_usdt': montant_usdt
    }

    df = pd.DataFrame([trade_data])
    if os.path.exists(HISTO_PATH):
        df.to_csv(HISTO_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(HISTO_PATH, index=False)

    with open(LOG_PATH, 'a') as f:
        f.write(f"[{now}] Trade {mode.upper()} | {action} {symbol} | {montant_usdt} USDT\n")

# ====== 🚀 MOTEUR PRINCIPAL ======
def run_predict_live(mode='fictif'):
    """Moteur principal de prédiction IA et d'exécution de trade."""
    print("📥 Lecture du fichier d'audit IA...")
    df = pd.read_csv(CSV_PATH)

    # Nettoyage éventuel
    df['score_ia'] = pd.to_numeric(df['score_ia'], errors='coerce')
    df.dropna(subset=['score_ia'], inplace=True)

    # Debug top 10
    print("🔝 Top cryptos par score IA :")
    print(df[['symbol', 'score_ia']].sort_values(by='score_ia', ascending=False).head(10))

    # Filtrage
    df_filtered = df[df['score_ia'] >= SCORE_MIN].sort_values(by='score_ia', ascending=False)

    if df_filtered.empty:
        print("⚠️ Aucune crypto avec un score IA suffisant.")
        return None

    top_crypto = df_filtered.iloc[0]
    symbol = top_crypto['symbol']
    score = top_crypto['score_ia']

    print(f"🏆 Meilleure crypto détectée : {symbol} avec un score IA de {score:.2f}")

    prediction, confidence = predict_price_movement(symbol)
    print(f"🤖 Prédiction IA pour {symbol} : {prediction} (confiance : {confidence:.2f})")

    execute_trade(symbol, mode)

    # TEMP : simule le vrai mouvement pour le log
    real_movement = prediction  # à remplacer plus tard par un check réel

    # Ajout : appelle de log_prediction avec toutes les infos enrichies
    log_prediction(
        symbol=symbol,
        score=score,
        proba=confidence,
        sentiment=top_crypto.get("sentiment", 0.5),
        var_1h=top_crypto.get("variation_1h", 0.0),
        prediction=prediction,
        real=real_movement,
        confidence=confidence,
        result="SUCCESS"  # ou "FAIL" selon le futur tracking réel
    )

    return {
        'symbol': symbol,
        'score_ia': score,
        'prediction': prediction,
        'confidence': confidence,
        'mode': mode
    }


# ====== 🧪 EXÉCUTION TEST ======
if __name__ == "__main__":
    result = run_predict_live(mode='fictif')
    if result:
        print(f"✅ Résultat : {result}")
