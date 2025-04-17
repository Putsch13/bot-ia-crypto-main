import pandas as pd
from datetime import datetime
from ml_brain import predict_price_movement
import os

# ====== 🔧 CONFIG ======
CSV_PATH = 'audit_100cryptos.csv'
HISTO_PATH = 'historique_trades.csv'
LOG_PATH = 'logs_robot.txt'
SCORE_MIN = 75  # Seuil minimum du score IA pour trader

# Simule une exécution de trade
def execute_trade(symbol, mode='fictif'):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action = 'BUY'
    montant_usdt = 100  # À adapter selon ta logique
    print(f"[{now}] 🛒 Exécution {mode.upper()} : {action} {symbol} pour {montant_usdt} USDT")

    # Log dans historique_trades.csv
    trade = {
        'timestamp': now,
        'symbol': symbol,
        'mode': mode,
        'action': action,
        'montant_usdt': montant_usdt
    }
    df = pd.DataFrame([trade])
    if os.path.exists(HISTO_PATH):
        df.to_csv(HISTO_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(HISTO_PATH, index=False)

    # Log texte
    with open(LOG_PATH, 'a') as f:
        f.write(f"[{now}] Trade {mode.upper()} | {action} {symbol} | {montant_usdt} USDT\n")


# ====== 🚀 MOTEUR PRINCIPAL ======
def run_predict_live(mode='fictif'):
    print("📥 Lecture du fichier d'audit IA...")
    df = pd.read_csv(CSV_PATH)

    # On filtre uniquement les cryptos avec un bon score IA
    df_filtered = df[df['score_ia'] >= SCORE_MIN].sort_values(by='score_ia', ascending=False)

    if df_filtered.empty:
        print("⚠️ Aucune crypto avec un score IA suffisant.")
        return None

    # On prend la top 1
    top_crypto = df_filtered.iloc[0]
    symbol = top_crypto['symbol']
    score = top_crypto['score_ia']

    print(f"🏆 Meilleure crypto détectée : {symbol} avec un score IA de {score}")

    # Prédiction ML sur cette crypto (confirmation)
    prediction = predict_price_movement(symbol)
    print(f"🤖 Prédiction IA pour {symbol} : {prediction}")

    # Exécution du trade (selon mode choisi)
    execute_trade(symbol, mode)

    # Résumé à renvoyer dans l’interface `/live`
    result = {
        'symbol': symbol,
        'score_ia': score,
        'prediction': prediction,
        'mode': mode
    }

    return result


# Exemple d’appel
if __name__ == "__main__":
    result = run_predict_live(mode='fictif')
    if result:
        print(f"✅ Résultat : {result}")
