import os
import csv
import json
import time
import threading
import logging
import joblib
import pandas as pd
import ccxt
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from audit_cryptos import get_ohlcv_df, enrichir_features


# === Modules internes
from audit_cryptos import run_full_audit
from backend_ia_bot import latest_ia_report, start_bot_from_api
from ml_brain import (
    analyse_technique, charger_modele,
    get_top_100_symbols, get_binance_ohlcv, enrichir_features, FEATURE_COLUMNS
)

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

@app.route("/top-predictions", methods=["GET"])
def top_predictions():
    try:
        model = joblib.load("models/model.pkl")
        scaler = joblib.load("models/scaler.pkl")
        label_encoder = joblib.load("models/label_encoder.pkl")

        symbols = get_top_100_symbols()
        logger.info(f"🔢 {len(symbols)} cryptos à analyser.")  # <- déjà présent, bien

        results = []

        for symbol in symbols:
            try:
                df = get_binance_ohlcv(symbol, limit=100)
                if df is None or df.empty:
                    continue

                df_enriched = enrichir_features(df)
                if df_enriched is None or df_enriched.empty:
                    continue

                current = df_enriched.iloc[-1]
                if current[FEATURE_COLUMNS[:-1]].isnull().any():
                    continue

                try:
                    symbol_encoded = label_encoder.transform([symbol])[0]
                except ValueError:
                    print(f"[SKIP] {symbol} ignoré : label inconnu pour l'IA")
                    continue

                row = {col: current[col] for col in FEATURE_COLUMNS[:-1]}
                row["symbol_encoded"] = symbol_encoded

                df_row = pd.DataFrame([row])
                df_scaled = scaler.transform(df_row)
                proba = float(model.predict_proba(df_scaled)[0][1])

                results.append({"symbol": symbol, "proba": round(proba, 4)})

            except Exception as e:
                continue

        results_sorted = sorted(results, key=lambda x: x["proba"], reverse=True)[:10]
        logger.info(f"✅ Rapport IA → {len(rows)} cryptos auditées avec succès.")
        return jsonify(results_sorted)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    import math

    def clean_dict(d):
        return {
            k: (0.0 if isinstance(v, float) and math.isnan(v) else v)
            for k, v in d.items()
        }

    try:
        if not latest_ia_report:
            return jsonify({"error": "Aucun rapport IA disponible."}), 404

        clean = {
            "timestamp": latest_ia_report.get("timestamp", str(datetime.utcnow())),
            "top": [clean_dict(dict(x)) for x in latest_ia_report.get("top", [])],
            "flop": [clean_dict(dict(x)) for x in latest_ia_report.get("flop", [])],
            "rapport": str(latest_ia_report.get("rapport", "Aucun rapport.")),
            "duration": int(latest_ia_report.get("duration", 0)),
        }
        return jsonify(clean)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/crypto_insight", methods=["GET"])
def get_crypto_insight():
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "Symbol manquant"}), 400

    try:
        df = get_binance_ohlcv(symbol, limit=1000)
        df = enrichir_features(df)
        df["symbol"] = symbol
        df, _ = encoder_symbols(df)
        latest = df.iloc[-1]

        insight = {
            "rsi": float(latest["rsi"]),
            "macd": float(latest["macd"]),
            "adx": float(latest["adx"]),
            "variation_1h": float(latest["variation_1h"]),
            "volume_ema": float(latest["volume_ema"]),
            "sentiment": float(latest.get("sentiment", 0.5)),
        }

        return jsonify(insight)

    except Exception as e:
        logger.error(f"[❌] Erreur /crypto_insight : {e}")
        return jsonify({"error": str(e)}), 500


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

    if errors:
        logger.warning("🧨 Résumé des erreurs d'audit :")
        for err in errors:
            logger.warning(f"  ⛔ {err}")


@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        with open("logs/trades.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            logs = list(reader)
            return jsonify(logs)
    except FileNotFoundError:
        return jsonify([]), 200  # fichier vide = tableau vide
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            "timestamp": datetime.utcnow().isoformat(),
            "top": top,
            "flop": flop,
            "rapport": rapport,
            "duration": 10
        }
        logger.info("✅ Audit IA terminé. Rapport prêt.")
    except Exception as e:
        logger.error("❌ Erreur audit IA auto : %s", e)

    threading.Timer(600, auto_audit_ia).start()

@app.route("/radar_data", methods=["GET"])
def get_radar_data():
    symbol = request.args.get("symbol", "BTCUSDT")
    try:
        df = get_ohlcv_df(symbol)
        if df is None or df.empty:
            return jsonify({"error": "Pas de données OHLCV."}), 404

        df = enrichir_features(df)
        if df is None or df.empty:
            return jsonify({"error": "Échec enrichissement."}), 500

        latest = df.iloc[-1]

        features = {
            "RSI": float(latest.get("rsi", 0)),
            "MACD": float(latest.get("macd", 0)),
            "Stoch RSI": float(latest.get("stoch_rsi", 0)),
            "ADX": float(latest.get("adx", 0)),
            "Volume EMA": float(latest.get("volume_ema", 0)),
            "Delta %": float(latest.get("delta_pct", 0)),
        }

        return jsonify({
            "symbol": symbol,
            "features": features
        })

    except Exception as e:
        logger.error(f"[Radar] Erreur pour {symbol} → {e}")
        return jsonify({"error": str(e)}), 500


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
