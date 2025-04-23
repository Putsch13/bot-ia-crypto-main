import pandas as pd
import joblib
from ml_brain import get_top_100_symbols, get_binance_ohlcv, enrichir_features, FEATURE_COLUMNS
import warnings

warnings.filterwarnings("ignore")

# === Chargement des modèles
model = joblib.load("models/model.pkl")
scaler = joblib.load("models/scaler.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")

# === Préparation
symbols = get_top_100_symbols()
predictions = []

print("🔍 Scan IA en cours sur 100 cryptos...")

for symbol in symbols:
    try:
        df = get_binance_ohlcv(symbol, limit=1500)
        if df is None or df.empty:
            continue

        df_enriched = enrichir_features(df)
        if df_enriched is None or df_enriched.empty:
            continue

        current = df_enriched.iloc[-1]

        # Vérif valeurs manquantes
        if current[FEATURE_COLUMNS[:-1]].isnull().any():
            continue

        # Encodage symbol
        symbol_encoded = label_encoder.transform([symbol])[0]

        # Construction ligne
        row = {col: current[col] for col in FEATURE_COLUMNS[:-1]}
        row["symbol_encoded"] = symbol_encoded

        df_row = pd.DataFrame([row])
        df_scaled = scaler.transform(df_row)

        # Prédiction proba
        proba = model.predict_proba(df_scaled)[0][1]  # proba que ça monte
        predictions.append((symbol, proba))

    except Exception as e:
        print(f"⚠️ {symbol} ignoré : {e}")
        continue

# === Affichage top 10
top_predictions = sorted(predictions, key=lambda x: x[1], reverse=True)[:10]

print("\n📈 TOP 10 cryptos IA (proba de montée) :\n")
for rank, (symbol, score) in enumerate(top_predictions, start=1):
    print(f"{rank:>2}. {symbol:<10} — 🚀 Proba: {score:.4f}")
