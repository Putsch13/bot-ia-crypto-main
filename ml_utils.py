# ml_utils.py
import joblib
import pandas as pd
from data_fetcher import fetch_enriched_features

model = joblib.load("models/model.pkl")
scaler = joblib.load("models/scaler.pkl")
label_encoder = joblib.load("models/label_encoder.pkl")

with open("models/feature_columns.txt") as f:
    FEATURE_COLUMNS = f.read().splitlines()

def predict_price_movement(symbol):
    df = fetch_enriched_features(symbol)
    if df is None or df.empty:
        return None, None

    current = df.iloc[-1]

    symbol_encoded = label_encoder.transform([symbol])[0]

    row = {col: current.get(col, 0) for col in FEATURE_COLUMNS if col != "symbol_encoded"}
    row["symbol_encoded"] = symbol_encoded

    df_row = pd.DataFrame([row])
    df_scaled = scaler.transform(df_row)

    proba = model.predict_proba(df_scaled)[0][1]
    prediction = "UP" if proba > 0.5 else "DOWN"
    return prediction, round(proba, 4)
