# backend_ia_bot.py

import os, json, threading, time, csv
from datetime import datetime
import pandas as pd
from flask import request, Flask
import ccxt
app = Flask(__name__)
from ml_utils import predict_price_movement
# === MODULES INTERNES ===
from audit_cryptos import run_full_audit
from ml_brain import charger_modele
from config import (
    SENTIMENT_FILE, LOG_FILE, TRADE_HISTORY_CSV,
    BINANCE_API_KEY, BINANCE_SECRET_KEY, USE_SANDBOX
)

def save_trade(symbol, buy_price, usdt_amount, mode="fictif"):
    symbol = symbol.replace("/", "")  # Nettoyage du format
    filename = "config/portefeuille.json"

    # Initialisation fichier si nécessaire
    if not os.path.exists(filename):
        portfolio = {"fictif": {}, "reel": {}}
    else:
        with open(filename, "r") as f:
            portfolio = json.load(f)

    # Création de l'entrée
    portfolio.setdefault(mode, {})[symbol] = {
        "achat": buy_price,
        "usdt": usdt_amount,
        "timestamp": datetime.now().timestamp()
    }

    # Sauvegarde
    with open(filename, "w") as f:
        json.dump(portfolio, f, indent=2)

    print(f"✅ Trade enregistré : {symbol} ({mode}) à {buy_price} pour {usdt_amount}$")

# === INIT VARIABLES ===
latest_ia_report = {}
model = charger_modele()
trending_list = []
stop_robot = False

exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY
})
exchange.set_sandbox_mode(USE_SANDBOX)

# === UTILS ===

def save_ia_data(data):
    with open(SENTIMENT_FILE, 'w') as f:
        json.dump(data, f)

def load_ia_data():
    try:
        with open(SENTIMENT_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[INFO] Aucun fichier IA existant : {e}")
        return {}

# === AUDIT LOOP ===

def audit_loop():
    global latest_ia_report
    while True:
        print("🔁 [AUTO] Lancement de l’audit IA...")
        try:
            start = time.time()
            top, flop, rapport = run_full_audit()
            result = {
                "top": top,
                "flop": flop,
                "rapport": rapport,
                "duration": int(time.time() - start),
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            latest_ia_report = result
            save_ia_data(result)
            print("✅ [AUTO] Audit IA mis à jour.")
        except Exception as e:
            print("❌ [AUTO] Erreur audit IA :", e)
        time.sleep(600)

# === IA CALCULATION ===

def calculer_score_crypto(ticker, symbol):
    sentiments = load_ia_data()
    variation_1h = ticker.get('percentage', 0)
    variation_24h = ticker.get('change', 0)
    volume = ticker.get('quoteVolume', 0)
    score = 0

    if variation_1h > 0: score += 20
    if variation_24h > 0: score += 30
    if volume > 1_000_000: score += 20
    if volume > 5_000_000: score += 30

    try:
        exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
        score += 5
    except Exception as e:
        print(f"[WARN] Pas de OHLCV pour {symbol} : {e}")

    coin = symbol.split("/")[0]
    if coin in trending_list:
        score += 15

    sentiment_score = sentiments.get(coin, {}).get("total", 0)
    score += round(sentiment_score * 10, 1)

    if model:
        try:
            label, proba = predict_price_movement(symbol.replace("/", ""))
            if label == "UP":
                score += 20
            else:
                score -= 10
        except Exception as e:
            print(f"[ERROR] Prédiction IA pour {symbol} : {e}")

    return min(score, 100)

# === LOGS & TRADES ===

def log_robot(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")

def enregistrer_trade(mode, crypto, prix_achat, prix_vente, gain_percent, resultat):
    file_exists = os.path.exists(TRADE_HISTORY_CSV)
    with open(TRADE_HISTORY_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "mode", "crypto", "prix_achat", "prix_vente", "gain_percent", "resultat"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mode, crypto,
            f"{prix_achat:.2f}", f"{prix_vente:.2f}",
            f"{gain_percent:.2f}%", resultat
        ])

# === BOT LOOP ===
PROBA_IA_SEUIL = {
    "safe": 0.7,
    "standard": 0.45,
    "risky": 0.25
}

@app.route("/radar_data")
def get_radar_data():
    symbol = request.args.get("symbol")
    # ... logic pour récupérer les features de ce symbol et renvoyer un JSON


def robot_loop(montant, variation, objectif, mode_exec, mode_type,
               seuil_entree=80, seuil_sortie=30, stop_loss_percent=10, reserve=0, profil='standard'):
    global stop_robot
    montant_courant = montant
    montant_initial = montant
    seuil_score = {"safe": 70, "standard": 50, "risky": 30}
    score_min = seuil_score.get(profil, 50)

    while not stop_robot:
        if montant_courant <= montant_initial * (1 - stop_loss_percent / 100):
            log_robot("🛑 Stop-loss déclenché.")
            break

        try:
            tickers = exchange.fetch_tickers()
        except Exception as e:
            log_robot(f"[ERROR] Tickeurs Binance échoués : {e}")
            time.sleep(600)
            continue

        candidates = []
        for symbol, ticker in tickers.items():
            if '/USDT' not in symbol or not ticker.get('last'):
                continue
            if abs(ticker.get('percentage', 0)) < variation:
                continue
            score = calculer_score_crypto(ticker, symbol)
            prediction, proba = "INCONNU", 0.0
            try:
                from ml_utils import predict_price_movement
                prediction, proba = predict_price_movement(symbol)
            except Exception as e:
                log_robot(f"[WARN] Prédiction IA échouée pour {symbol} : {e}")

            if score >= score_min and proba >= PROBA_IA_SEUIL.get(profil, 0.45):
                ticker['score'] = score
                ticker['symbol'] = symbol
                ticker['proba'] = proba
                ticker['prediction'] = prediction
                candidates.append(ticker)


        if not candidates:
            log_robot("🔍 Aucune crypto sélectionnée. Attente 10 min...")
            time.sleep(600)
            continue

        best = sorted(candidates, key=lambda x: x['score'], reverse=True)[0]
        symbole = best['symbol']
        

        try:
            prix_achat = exchange.fetch_ticker(symbole)['last']
            
        except Exception as e:
            log_robot(f"[ERROR] Prix indisponible pour {symbole} : {e}")
            time.sleep(600)
            continue

        save_trade(symbole, prix_achat, montant_courant, mode_exec)


        log_robot(f"🧪 Achat {'réel' if mode_exec != 'fictif' else 'fictif'} de {symbole} à {prix_achat:.2f}")
        prix_vente = prix_achat * (1 + objectif / 100)
        gain = prix_vente - prix_achat
        gain_percent = (gain / prix_achat) * 100
        enregistrer_trade(mode_exec, symbole, prix_achat, prix_vente, gain_percent, "Cycle complet")

        if mode_type == "compose":
            montant_courant += gain * 0.5
        elif mode_type == "auto":
            montant_courant += gain
        else:
            break

        log_robot(f"💹 Nouveau capital : {montant_courant:.2f} USDT")
        time.sleep(10)

# === FLASK ENTRYPOINTS ===

def start_bot_from_api():
    global stop_robot
    stop_robot = False
    try:
        data = request.get_json() or {}
        print("📥 Paramètres reçus par le bot :", data)
        thread = threading.Thread(target=robot_loop, args=(
            float(data.get("montant", 100)),
            float(data.get("variation_entree", 1.5)),
            float(data.get("objectif_gain", 3)),
            data.get("mode_execution", "fictif"),
            data.get("mode_auto", "auto"),
            float(data.get("seuil_entree", 80)),
            float(data.get("seuil_sortie", 40)),
            float(data.get("stop_loss", 10)),
            float(data.get("reserve", 0)),
            data.get("profil", "standard"),
        ))
        thread.start()
        return {"status": "✅ Robot IA lancé avec succès."}
    except Exception as e:
        log_robot(f"[ERROR] Lancement du bot : {e}")
        return {"status": "❌ Erreur lancement bot", "error": str(e)}

def stop_bot_from_api():
    global stop_robot
    stop_robot = True
    log_robot("🛑 Robot stoppé via API.")
    return {"status": "🛑 Robot stoppé"}

def get_trending_coins():
    try:
        return get_top_100_symbols()[:50]
    except Exception as e:
        print(f"Erreur trending coins : {e}")
        return []


# === LANCEMENT AUTO AUDIT ===

audit_thread = threading.Thread(target=audit_loop, daemon=True)
audit_thread.start()
print("🧠 Système IA + Audit lancé en tâche de fond.")
