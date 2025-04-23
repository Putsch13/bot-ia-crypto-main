import pandas as pd
import joblib
import numpy as np
from sklearn.metrics import log_loss
from ml_brain import FEATURE_COLUMNS

def audit_model_confidence():
    df = pd.read_csv("dataset_trades.csv")
    model = joblib.load("models/model.pkl")
    scaler = joblib.load("models/scaler.pkl")

    X = df[FEATURE_COLUMNS]
    y = df["target"]
    X_scaled = scaler.transform(X)

    y_proba = model.predict_proba(X_scaled)[:, 1]
    y_pred = model.predict(X_scaled)

    print("🔍 Audit des prédictions IA :")
    print("➡️ Moyenne proba UP :", round(np.mean(y_proba), 4))
    print("➡️ Écart-type proba :", round(np.std(y_proba), 4))
    print("➡️ LogLoss :", round(log_loss(y, y_proba), 4))
    print("➡️ % prédits UP :", round(np.mean(y_pred == 1) * 100, 2), "%")
