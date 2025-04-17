import os
import threading
import time
import csv
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ccxt
import pandas as pd

# === Modules internes ===
from audit_cryptos import run_full_audit
from backend_ia_bot import latest_ia_report, start_bot_from_api
from ml_brain import analyse_technique, charger_modele
from config import (
    BINANCE_API_KEY, BINANCE_SECRET_KEY, USE_SANDBOX,
    DATA_PATH, MODELS_PATH, LOG_FILE, TRADE_HISTORY_CSV,
    SENTIMENT_FILE, IA_CONFIDENCE_THRESHOLD
)
from ai_engine import predict_from_csv, train_model
from bot_config import load_config, save_config
from bot_runner import run_bot

# === Flask Setup ===
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# === Logger ===
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# === Binance / modèle ===
exchange = ccxt.binance({'apiKey': BINANCE_API_KEY, 'secret': BINANCE_SECRET_KEY})
exchange.set_sandbox_mode(USE_SANDBOX)
model = charger_modele()

# === Routes API ===
@app.route("/status", methods=["GET"])
def get_status():
    try:
        return jsonify({
            "message": "🧠 Backend opérationnel",
            "audit": latest_ia_report if latest_ia_report else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_config", methods=["GET"])
def get_config():
    try:
        return jsonify({"message": "OK", "config": load_config()})
    except Exception as e:
        return jsonify({"message": f"Erreur : {e}", "config": {}}), 500

@app.route("/set_config", methods=["POST"])
def set_config():
    try:
        new_config = request.json
        if not new_config:
            return jsonify({"message": "Aucune donnée reçue"}), 400
        save_config(new_config)
        return jsonify({"message": "✅ Configuration mise à jour"})
    except Exception as e:
        return jsonify({"message": f"Erreur : {e}"}), 500

@app.route("/get_portfolio", methods=["GET"])
def get_portfolio():
    try:
        with open("config/portefeuille.json", "r") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"fictif": {}, "reel": {}})

@app.route("/stop_trade", methods=["POST"])
def stop_trade():
    data = request.json
    symbol = data.get("symbol")
    mode = data.get("mode")
    try:
        with open("config/portefeuille.json", "r") as f:
            portfolio = json.load(f)
        if symbol in portfolio.get(mode, {}):
            del portfolio[mode][symbol]
            with open("config/portefeuille.json", "w") as f:
                json.dump(portfolio, f, indent=2)
            return jsonify({"status": "ok"})
        return jsonify({"error": "Symbol non trouvé"}), 404
    except FileNotFoundError:
        return jsonify({"error": "Aucun portefeuille trouvé"}), 400

@app.route("/ping")
def ping():
    return "pong"

@app.route("/start_bot", methods=["POST"])
def api_start_bot():
    try:
        response = start_bot_from_api()
        logger.info("API /start_bot appelée. Réponse : %s", response)
        return jsonify(response)
    except Exception as e:
        logger.error("Erreur /start_bot : %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/rapport_ia", methods=["GET"])
def api_rapport_ia():
    return jsonify(latest_ia_report or {})

@app.route("/performance", methods=["GET"])
def get_performance_summary():
    try:
        with open(TRADE_HISTORY_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            trades = list(reader)
        if not trades:
            return jsonify({"message": "Aucun trade.", "data": {}})
        total = len(trades)
        gains = [float(t["Gain (%)"].replace("%", "").replace(",", ".")) for t in trades]
        df = pd.DataFrame([(t["Date"].split(" ")[0], g) for t, g in zip(trades, gains)], columns=["date", "gain"])
        evolution = df.groupby("date")["gain"].sum().reset_index().to_dict(orient="records")
        return jsonify({
            "message": "OK",
            "data": {
                "total_trades": total,
                "total_gain": round(sum(gains), 2),
                "winrate": round(len([g for g in gains if g > 0]) / total * 100, 1),
                "gains_by_day": evolution
            }
        })
    except Exception as e:
        logger.error("Erreur /performance : %s", e)
        return jsonify({"message": f"Erreur : {e}", "data": {}}), 500

@app.route("/topflop", methods=["GET"])
def get_top_flop():
    try:
        with open("logs/trades.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            latest_trades = {}
            for t in reversed(list(reader)):
                sym = t["Symbol"]
                if sym not in latest_trades:
                    latest_trades[sym] = t
            top = []
            flop = []
            for sym, trade in latest_trades.items():
                try:
                    variation = float(trade["Gain (%)"].replace("%", "").replace(",", "."))
                    entry = {"symbol": sym, "variation": variation}
                    (top if variation >= 0 else flop).append(entry)
                except:
                    continue
            top = sorted(top, key=lambda x: x["variation"], reverse=True)[:5]
            flop = sorted(flop, key=lambda x: x["variation"])[:5]
            return jsonify({"top": top, "flop": flop})
    except Exception as e:
        logger.error(f"Erreur /topflop : {e}")
        return jsonify({"top": [], "flop": []})

@app.route("/get_positions", methods=["GET"])
def get_positions():
    try:
        with open("positions.json", "r") as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify([])

@app.route("/sell_position", methods=["POST"])
def sell_position():
    symbol = request.json.get("symbol")
    try:
        with open("positions.json", "r") as f:
            positions = json.load(f)
        positions = [p for p in positions if p["symbol"] != symbol]
        with open("positions.json", "w") as f:
            json.dump(positions, f)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/predict", methods=["GET"])
def predict():
    symbol = request.args.get("symbol")
    tf = request.args.get("tf")
    if not symbol or not tf:
        return jsonify({"error": "Paramètre 'symbol' ou 'tf' manquant."}), 400
    try:
        result = predict_from_csv(f"{DATA_PATH}/{symbol}_{tf}.csv", f"{MODELS_PATH}/xgb_{symbol}_{tf}.model")
        return jsonify(result)
    except Exception as e:
        logger.error("Erreur prédiction IA : %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/train", methods=["GET"])
def train():
    symbol = request.args.get("symbol")
    tf = request.args.get("tf")
    if not symbol or not tf:
        return jsonify({"error": "Paramètres requis : ?symbol=XXX&tf=XXX"}), 400
    try:
        _, acc = train_model(f"{DATA_PATH}/{symbol}_{tf}.csv", f"{MODELS_PATH}/xgb_{symbol}_{tf}.model")
        return jsonify({"symbol": symbol, "tf": tf, "status": "✅ Entraînement terminé", "accuracy": round(acc, 4)})
    except Exception as e:
        return jsonify({"symbol": symbol, "tf": tf, "status": "❌ Erreur", "error": str(e)}), 500

# === Audit IA auto
def auto_audit_ia():
    global latest_ia_report
    try:
        logger.info("🧠 Lancement de l’audit IA auto...")
        top, flop, rapport = run_full_audit()
        latest_ia_report = {
            "top": top,
            "flop": flop,
            "rapport": rapport,
            "duration": 10
        }
        logger.info("✅ Audit IA terminé.")
    except Exception as e:
        logger.error("❌ Erreur audit IA auto : %s", e)
    threading.Timer(600, auto_audit_ia).start()

# === Frontend
@app.route("/")
def serve_index():
    return send_from_directory("frontend_dist", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("frontend_dist", path)

# === RUN Flask ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    logger.info(f"🧠 Lancement Flask sur le port {port}")
    auto_audit_ia()
    app.run(host="0.0.0.0", port=port, debug=False)
