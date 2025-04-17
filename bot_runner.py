import os
import time
import csv
from datetime import datetime
from data_fetcher import fetch_real_data
from bot_config import load_config, load_portfolio, save_portfolio
import ccxt
from bot_config import charger_portefeuille, sauvegarder_portefeuille

def run_bot(mode="fictif", profil="moyen", capital=1000, take_profit=5):
    print(f"[MODE BOT] Lancement du bot en mode : {mode.upper()}")
    
    # Charger le portefeuille correspondant
    portefeuille = charger_portefeuille(mode)

    # Récupérer les signaux IA
    recommandations = get_signaux_ia(profil)

    for reco in recommandations:
        symbol = reco["symbol"]
        action = reco["action"]
        montant = capital / len(recommandations)  # Split équitable

        if mode == "reel":
            executer_trade_reel(symbol, action, montant)
        else:
            executer_trade_fictif(symbol, action, montant)

    sauvegarder_portefeuille(portefeuille, mode)
    return {"mode": mode, "trades": len(recommandations)}

def executer_trade_reel(symbol, action, montant):
    print(f"💸 TRADE RÉEL → {action.upper()} {symbol} pour {montant}$")
    # Ici : appel ccxt create_order (à faire plus tard)

def executer_trade_fictif(symbol, action, montant):
    print(f"🧪 TRADE FICTIF → {action.upper()} {symbol} pour {montant}$")
    prix = get_prix_binance(symbol)  # données réelles
    # Calculer simulation
    # Mettre à jour portefeuille fictif
    # Logguer dans logs CSV

def get_top_cryptos(limit=100):
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if s.endswith("/USDT") and ":" not in s]
    return usdt_pairs[:limit]

TRADE_HISTORY_CSV = "logs/trades.csv"

def log_trade(symbol, prix_achat, prix_vente, montant, pnl_usdt, variation):
    os.makedirs("logs", exist_ok=True)
    file_exists = os.path.isfile(TRADE_HISTORY_CSV)

    with open(TRADE_HISTORY_CSV, "a", newline="") as csvfile:
        fieldnames = ["Date", "Crypto", "Achat", "Vente", "Montant", "Variation (%)", "Gain ($)"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Crypto": symbol,
            "Achat": round(prix_achat, 4),
            "Vente": round(prix_vente, 4),
            "Montant": round(montant, 2),
            "Variation (%)": round(variation * 100, 2),
            "Gain ($)": round(pnl_usdt, 2)
        })

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

                log_trade(symbol, prix_achat, prix_actuel, montant, pnl, variation_depuis_achat)

                if config["mode"] == "automatique_composé":
                    gains_total = portfolio.get("gains_composés", 0)
                    gains_total += pnl
                    portfolio["gains_composés"] = gains_total

                del portfolio[symbol]

    save_portfolio(portfolio)

def start_bot_loop(interval_sec=300):
    while True:
        print("[⚙️ BOT] Nouvelle itération IA")
        run_bot_cycle()
        time.sleep(interval_sec)

if __name__ == "__main__":
    start_bot_loop()
