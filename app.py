
import os
import csv
import json
import time
import threading
import logging
import joblib
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

# === Modules internes
from audit_cryptos import get_ohlcv_df, enrichir_features, run_full_audit
from backend_ia_bot import latest_ia_report, start_bot_from_api
from ml_brain import (
    charger_modele,
    get_top_100_symbols, get_binance_ohlcv,
    enrichir_features, FEATURE_COLUMNS, charger_et_predire_from_df
)
from config import (
    BINANCE_API_KEY, BINANCE_SECRET_KEY, USE_SANDBOX,
    DATA_PATH, MODELS_PATH, LOG_FILE, TRADE_HISTORY_CSV,
    SENTIMENT_FILE, IA_CONFIDENCE_THRESHOLD
)
from ai_engine import predict_from_csv, train_model
from bot_config import load_config, save_config, load_portfolio, charger_portefeuille, sauvegarder_portefeuille
from bot_runner import run_bot
from data_fetcher import fetch_real_data, get_prix_binance, fetch_enriched_features
from ml_brain import predict_price_movement

# === App Flask ===
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# === Logger ===
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# === Binance Client ===
exchange = ccxt.binance({'apiKey': BINANCE_API_KEY, 'secret': BINANCE_SECRET_KEY})
exchange.set_sandbox_mode(USE_SANDBOX)

# === Chargement du modèle IA ===
model = joblib.load("models/model.pkl")
scaler = joblib.load("models/scaler.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")
with open("models/feature_columns.txt") as f:
    FEATURE_COLUMNS = f.read().splitlines()
# 🛠️ Début de l'app Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

portefeuille = charger_portefeuille("prod")
capital_total = 1000  # ou ton capital réel

symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", ...]  # ou ta liste dynamique

@app.route("/run_ai_bot", methods=["POST"])
def lancer_bot_ia():
    try:
        portefeuille = charger_portefeuille("prod")
        capital_total = 1000  # ou un paramètre dynamique
        top_symbols = get_top_100_symbols()

        verifier_et_exec_trading(top_symbols, portefeuille, capital_total)
        return jsonify({"message": "🤖 IA trading lancé avec succès"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

TRADE_HISTORY_CSV = "logs/trades.csv"
PREDICTIONS_LOG_CSV = "logs/ia_predictions_log.csv"

# 🔁 NOUVEAU FORMAT UNIFIÉ
PREDICTION_FIELDS = [
    "Date", "Symbol", "Score", "Probabilité", "Sentiment", "Variation_1h",
    "Prediction", "Real", "Confidence", "Result"
]

# === Chargement des modèles ML ===
model = joblib.load("models/model.pkl")
scaler = joblib.load("models/scaler.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")
with open("models/feature_columns.txt") as f:
    FEATURE_COLUMNS = f.read().splitlines()

# === PROFIL UTILISATEUR ===
# Définir des seuils par profil IA
PROFILS_IA = {
    "prudent": 0.7,
    "moyen": 0.6,
    "agressif": 0.5
}



def log_prediction(symbol, score, proba, sentiment, var_1h, prediction=None, real=None, confidence=None, result=None):
    os.makedirs("logs", exist_ok=True)
    file_exists = os.path.isfile(PREDICTIONS_LOG_CSV)

    with open(PREDICTIONS_LOG_CSV, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=PREDICTION_FIELDS)
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

@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    try:
        if not os.path.exists(PREDICTIONS_LOG_CSV):
            print("📂 Fichier de log manquant : logs/ia_predictions_log.csv")
            return jsonify([])

        with open(PREDICTIONS_LOG_CSV, "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return jsonify(data)

    except Exception as e:
        print("🔥 Erreur interne API /api/predictions:", e)
        return jsonify([]), 500

# ✅ AJOUT : GET FEATURES ENRICHIES
@app.route("/api/features/<symbol>", methods=["GET"])
def get_enriched_features(symbol):
    try:
        df = fetch_enriched_features(symbol.upper())
        if df is None or df.empty:
            return jsonify({"error": "Aucune donnée"}), 404
        return jsonify(df.iloc[-1].to_dict())
    except Exception as e:
        print(f"Erreur features enrichies pour {symbol}:", e)
        return jsonify({"error": "Erreur interne"}), 500    

# ✅ AJOUT : GET PRIX DIRECT
@app.route("/api/price/<symbol>", methods=["GET"])
def get_price(symbol):
    try:
        price = get_prix_binance(symbol.upper())
        if price is None:
            return jsonify({"error": "Prix introuvable"}), 404
        return jsonify({"symbol": symbol.upper(), "price": price})
    except Exception as e:
        print(f"Erreur récupération prix pour {symbol}:", e)
        return jsonify({"error": "Erreur interne"}), 500
                 

# === Flask Setup ===
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# === Logger ===
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# === Binance Client ===
exchange = ccxt.binance({'apiKey': BINANCE_API_KEY, 'secret': BINANCE_SECRET_KEY})
exchange.set_sandbox_mode(USE_SANDBOX)

# === Chargement du modèle IA
model = charger_modele()

# === API : Prédictions IA logs CSV
@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    try:
        if not os.path.exists(PREDICTIONS_LOG_CSV):
            print("📂 Fichier de log manquant : logs/ia_predictions_log.csv")
            return jsonify([])

        with open(PREDICTIONS_LOG_CSV, "r") as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return jsonify(data)

    except Exception as e:
        print("🔥 Erreur interne API /api/predictions:", e)
        return jsonify([]), 500


@app.route('/api/score_ia_du_jour', methods=['GET'])
def score_ia_du_jour():
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        with open('logs/ia_predictions_log.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            today_preds = [row for row in reader if row['Date'].startswith(today)]

        if not today_preds:
            return jsonify({'score': None, 'message': 'Aucune prédiction aujourd’hui.'})

        total = len(today_preds)
        success = sum(1 for p in today_preds if p['result'] == 'SUCCESS')
        score = round((success / total) * 100)

        return jsonify({'score': score, 'success': success, 'total': total})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === API : Divers
@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({"message": "🧠 Backend opérationnel", "audit": latest_ia_report or None})

@app.route("/ping")
def ping():
    return "pong"

# === API : Configuration / Portefeuille
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

# === API : IA & Audit
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

@app.route("/top-predictions", methods=["GET"])
def top_predictions():
    try:
        symbols = get_top_100_symbols()
        results = []

        for symbol in symbols:
            try:
                df = get_binance_ohlcv(symbol, limit=1500)
                if df is None or df.empty:
                    continue

                df_enriched = enrichir_features(df)
                if df_enriched is None or df_enriched.empty:
                    continue

                df_enriched["symbol"] = symbol
                df_enriched["symbol_encoded"] = label_encoder.transform([symbol])[0]

                pred_score = charger_et_predire_from_df(df_enriched)
                if pred_score.empty:
                    continue
                proba = float(pred_score["confidence"].iloc[-1])

                results.append({"symbol": symbol, "proba": round(proba, 4)})
            except Exception as ex:
                logger.warning(f"Erreur sur {symbol}: {ex}")
                continue

        results_sorted = sorted(results, key=lambda x: x["proba"], reverse=True)[:10]
        return jsonify(results_sorted)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Auto audit IA en boucle
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
        logger.info("✅ Audit IA terminé.")
    except Exception as e:
        logger.error("❌ Erreur audit IA auto : %s", e)

    threading.Timer(600, auto_audit_ia).start()

# === FRONTEND Static
@app.route("/")
def serve_index():
    return send_from_directory("frontend_dist", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("frontend_dist", path)

@app.route("/score_ia_du_jour")
def get_score_ia():
    try:
        df = pd.read_csv("dataset_trades.csv")
        model = joblib.load("models/model.pkl")
        scaler = joblib.load("models/scaler.pkl")
        from ml_brain import FEATURE_COLUMNS

        X = df[FEATURE_COLUMNS]
        y = df["target"]
        X_scaled = scaler.transform(X)
        y_proba = model.predict_proba(X_scaled)[:, 1]
        mean_proba = np.mean(y_proba)

        return {"score": round(mean_proba * 100, 1)}
    except Exception as e:
        return {"score": None, "error": str(e)}

@app.route("/performance")
def performance():
    try:
        if not os.path.exists("logs/ia_predictions_log.csv"):
            return {"data": {"total_gain": 0, "daily_gain": 0, "total_trades": 0}}

        df = pd.read_csv("logs/ia_predictions_log.csv")
        df["gain"] = df["prix_vente"] - df["prix_achat"]
        total_gain = df["gain"].sum()
        total_trades = len(df)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            daily = df.groupby(df["date"].dt.date)["gain"].sum().reset_index()
            gains_by_day = [{"date": str(row["date"]), "gain": row["gain"]} for _, row in daily.iterrows()]
            last_day_gain = gains_by_day[-1]["gain"] if gains_by_day else 0
        else:
            gains_by_day = []
            last_day_gain = 0

        return {
            "data": {
                "total_gain": round(total_gain, 2),
                "daily_gain": round(last_day_gain, 2),
                "total_trades": total_trades,
                "gains_by_day": gains_by_day
            }
        }
    except Exception as e:
        return {"data": {}, "error": str(e)}

@app.route("/radar_data")
def radar_data():
    try:
        symbol = request.args.get("symbol", "BTCUSDT")
        from ml_brain import get_binance_ohlcv, enrichir_features
        df = get_binance_ohlcv(symbol.replace("/", ""), interval="1m", limit=1500)
        df = enrichir_features(df)
        last_row = df.iloc[-1].to_dict()

        radar_fields = [
            "rsi", "stoch_rsi", "macd", "macd_diff", "adx", "bollinger_width",
            "volume", "volume_ema", "delta_pct", "variation", "upper_shadow", "lower_shadow"
        ]
        result = {field: float(last_row.get(field, 0)) for field in radar_fields}
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logs/ia_predictions_log.csv")
def serve_log():
    try:
        return send_file("logs/ia_predictions_log.csv", mimetype="text/csv")
    except:
        return "Fichier non trouvé", 404

@app.route("/logs")
def list_logs():
    try:
        files = os.listdir("logs")
        return jsonify(files)
    except:
        return jsonify([])

@app.route("/api/stats_ia")
def api_stats_ia():
    try:
        df = pd.read_csv("dataset_trades.csv")
        model = joblib.load("models/model.pkl")
        scaler = joblib.load("models/scaler.pkl")
        from ml_brain import FEATURE_COLUMNS
        from sklearn.metrics import log_loss

        X = df[FEATURE_COLUMNS]
        y = df["target"]
        X_scaled = scaler.transform(X)
        y_proba = model.predict_proba(X_scaled)[:, 1]
        y_pred = model.predict(X_scaled)

        return {
            "mean_proba": round(float(np.mean(y_proba)), 4),
            "std_proba": round(float(np.std(y_proba)), 4),
            "log_loss": round(float(log_loss(y, y_proba)), 4),
            "percent_up": round(float(np.mean(y_pred == 1)) * 100, 2)
        }
    except Exception as e:
        return {"error": str(e)}

@app.route("/run_prediction_now", methods=["POST"])
def run_prediction_now():
    from predict_live import run_predict_live

    try:
        mode = request.json.get("mode", "fictif")
        result = run_predict_live(mode=mode)
        if not result:
            return jsonify({"status": "fail", "message": "Aucune crypto avec un bon score IA."}), 200

        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        logger.error(f"❌ Erreur /run_prediction_now : {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/stats_ia")
def get_stats_ia():
    from ml_brain import audit_model_confidence
    import pandas as pd
    import joblib
    import numpy as np
    from sklearn.metrics import log_loss

    try:
        df = pd.read_csv("dataset_trades.csv")
        model = joblib.load("models/model.pkl")
        scaler = joblib.load("models/scaler.pkl")

        with open("models/feature_columns.txt", "r") as f:
            feature_cols = [line.strip() for line in f.readlines()]

        X = df[feature_cols]
        y = df["target"]
        X_scaled = scaler.transform(X)

        y_proba = model.predict_proba(X_scaled)[:, 1]
        y_pred = model.predict(X_scaled)

        return {
            "mean_proba": round(np.mean(y_proba), 4),
            "std_proba": round(np.std(y_proba), 4),
            "log_loss": round(log_loss(y, y_proba), 4),
            "percent_up": round(np.mean(y_pred == 1) * 100, 2),
        }

    except Exception as e:
        return {"error": str(e)}, 500

# === FLASK RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    logger.info(f"🧠 Lancement Flask sur le port {port}")
    auto_audit_ia()
    app.run(host="0.0.0.0", port=port, debug=False)
