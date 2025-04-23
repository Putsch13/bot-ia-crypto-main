import os
import time
import csv
from datetime import datetime
from flask import Flask, request, jsonify
from data_fetcher import fetch_real_data, get_prix_binance
from bot_config import load_config, load_portfolio, save_portfolio
from bot_config import charger_portefeuille, sauvegarder_portefeuille
import ccxt
from ml_brain import predict_price_movement

app = Flask(__name__)

TRADE_HISTORY_CSV = "logs/trades.csv"


def verifier_et_exec_trading(symbols, portefeuille, capital_dispo, seuil_profit=0.03):
    for symbol in symbols:
        try:
            prediction, proba = predict_price_movement(symbol)
            print(f"🤖 {symbol} → Prediction IA : {prediction} ({proba*100:.2f}%)")

            if prediction == "UP" and proba >= 0.6 and symbol not in portefeuille:
                prix_achat = get_prix_binance(symbol)
                montant = capital_dispo * 0.1  # 10% du capital
                if prix_achat:
                    portefeuille[symbol] = {
                        "achat": prix_achat,
                        "usdt": montant,
                        "timestamp": time.time(),
                        "min_profit_pct": seuil_profit
                    }
                    print(f"🟢 Achat {symbol} à {prix_achat} USDT")
                    sauvegarder_portefeuille(portefeuille)
        except Exception as e:
            print(f"❌ Erreur analyse {symbol} : {e}")

    for symbol, pos in list(portefeuille.items()):
        prix_actuel = get_prix_binance(symbol)
        if prix_actuel:
            variation = (prix_actuel - pos["achat"]) / pos["achat"]
            if variation >= pos.get("min_profit_pct", seuil_profit):
                print(f"💰 Vente {symbol} → +{variation*100:.2f}%")
                del portefeuille[symbol]
                sauvegarder_portefeuille(portefeuille)

def log_trade_en_attente(symbol, prix_achat, montant, mode):
    os.makedirs("logs", exist_ok=True)
    file_exists = os.path.isfile(TRADE_HISTORY_CSV)

    with open(TRADE_HISTORY_CSV, "a", newline="") as csvfile:
        fieldnames = ["Date", "Mode", "Crypto", "Prix_achat", "Prix_vente", "Gain (%)", "Résultat"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Mode": mode,
            "Crypto": symbol,
            "Prix_achat": round(prix_achat, 4),
            "Prix_vente": "",
            "Gain (%)": "",
            "Résultat": "⏳ En attente"
        })

def update_trade_result(symbol, prix_achat, prix_vente, variation):
    lignes = []
    with open(TRADE_HISTORY_CSV, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["Crypto"] == symbol and row["Prix_achat"] == str(round(prix_achat, 4)) and row["Résultat"] == "⏳ En attente":
                row["Prix_vente"] = round(prix_vente, 4)
                row["Gain (%)"] = f"{round(variation * 100, 2)}%"
                row["Résultat"] = "✅ Exécuté"
            lignes.append(row)

    with open(TRADE_HISTORY_CSV, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=lignes[0].keys())
        writer.writeheader()
        writer.writerows(lignes)

def executer_trade_fictif(symbol, action, montant, mode="fictif"):
    prix_achat = get_prix_binance(symbol)
    log_trade_en_attente(symbol, prix_achat, montant, mode)

    portefeuille = charger_portefeuille(mode)
    portefeuille[symbol] = {
        "achat": prix_achat,
        "usdt": montant,
        "timestamp": time.time()
    }
    sauvegarder_portefeuille(portefeuille, mode)

    print(f"[📥 POSITION OUVERTE] {symbol} à {prix_achat} pour {montant} USDT")

def vendre_trade_fictif(symbol, mode="fictif"):
    portefeuille = charger_portefeuille(mode)
    if symbol not in portefeuille:
        print(f"Aucune position trouvée pour {symbol}")
        return False

    position = portefeuille[symbol]
    prix_achat = position["achat"]
    montant = position["usdt"]
    prix_vente = get_prix_binance(symbol)

    variation = (prix_vente - prix_achat) / prix_achat
    pnl = variation * montant

    print(f"[🔴 VENTE MANUELLE] {symbol} à {prix_vente} | PnL: {round(pnl, 2)} USDT")

    update_trade_result(symbol, prix_achat, prix_vente, variation)
    del portefeuille[symbol]
    sauvegarder_portefeuille(portefeuille, mode)
    return True

def get_top_cryptos(limit=100):
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if s.endswith("/USDT") and ":" not in s]
    return usdt_pairs[:limit]

def run_bot(mode="fictif", profil="moyen", capital=1000, take_profit=5):
    print(f"[MODE BOT] Lancement du bot en mode : {mode.upper()}")
    portefeuille = charger_portefeuille(mode)
    recommandations = []
    seuil = {"prudent": 0.7, "moyen": 0.6, "agressif": 0.5}.get(profil, 0.6)
    for symbol in get_top_cryptos():
        pred, proba = predict_price_movement(symbol)
        if pred == "UP" and proba >= seuil:
            recommandations.append({"symbol": symbol, "action": "buy"})

    for reco in recommandations:
        symbol = reco["symbol"]
        action = reco["action"]
        montant = capital / len(recommandations)

        if mode == "reel":
            executer_trade_reel(symbol, action, montant)
        else:
            executer_trade_fictif(symbol, action, montant, mode)

    sauvegarder_portefeuille(portefeuille, mode)
    return {"mode": mode, "trades": len(recommandations)}

def run_bot_cycle():
    config = load_config()
    portfolio = load_portfolio()
    cryptos = get_top_cryptos(limit=100)

    for symbol in cryptos:
        print(f"[BOT] Analyse de {symbol}...")

        data = fetch_real_data(symbol)
        if data is None:
            continue

        variation = data["variation_1h"]
        prix_actuel = data["sma_10"]

        if symbol not in portfolio:
            if variation >= config["seuil_entree"]:
                montant = config["capital_total"] * 0.1

                if config["mode"] == "automatique_composé":
                    gains = portfolio.get("gains_composés", 0)
                    montant += gains

                portfolio[symbol] = {
                    "achat": prix_actuel,
                    "usdt": montant,
                    "timestamp": time.time()
                }
                print(f"[🟢 ACHAT] {symbol} à {prix_actuel} pour {montant} USDT")

        else:
            prix_achat = portfolio[symbol]["achat"]
            variation_depuis_achat = (prix_actuel - prix_achat) / prix_achat

            if variation_depuis_achat <= config["seuil_sortie_perte"] or variation_depuis_achat >= config["seuil_sortie_gain"]:
                montant = portfolio[symbol]["usdt"]
                pnl = variation_depuis_achat * montant

                print(f"[🔴 VENTE] {symbol} à {prix_actuel} | PnL: {round(pnl, 2)} USDT")

                update_trade_result(symbol, prix_achat, prix_actuel, variation_depuis_achat)

                if config["mode"] == "automatique_composé":
                    gains_total = portfolio.get("gains_composés", 0)
                    gains_total += pnl
                    portfolio["gains_composés"] = gains_total

                del portfolio[symbol]

    save_portfolio(portfolio)

@app.route("/vendre_trade", methods=["POST"])
def vendre_trade():
    data = request.get_json()
    symbol = data.get("symbol")
    mode = data.get("mode", "fictif")

    success = vendre_trade_fictif(symbol, mode)
    return jsonify({"success": success})

if __name__ == "__main__":
    app.run(debug=True, port=5002)
