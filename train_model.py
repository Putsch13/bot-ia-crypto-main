import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, log_loss
import os

# === Chargement des données ===
df = pd.read_csv("dataset_trades.csv")

# === Encodage du symbol si besoin ===
if "symbol_encoded" not in df.columns:
    le = LabelEncoder()
    df["symbol_encoded"] = le.fit_transform(df["symbol"])
    joblib.dump(le, "models/label_encoder.pkl")
else:
    le = None  # Optionnel si déjà présent

# === Sélection des features ===
FEATURE_COLUMNS = [
    col for col in df.columns if col not in ["target", "symbol", "risk_profile", "risk_profile_encoded"]
]

# === Mise à jour du fichier de colonnes ===
os.makedirs("models", exist_ok=True)
with open("models/feature_columns.txt", "w") as f:
    f.write("\n".join(FEATURE_COLUMNS))

X = df[FEATURE_COLUMNS]
y = df["target"]

# === Normalisation ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, "models/scaler.pkl")

# === Train/Test Split ===
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# === Entraînement du modèle avec gestion du déséquilibre ===
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)
joblib.dump(model, "models/model.pkl")

# === Évaluation ===
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("\n=== Rapport de classification ===")
print(classification_report(y_test, y_pred))

print("\n=== Matrice de confusion ===")
print(confusion_matrix(y_test, y_pred))

print("\n=== Log Loss ===")
print(round(log_loss(y_test, y_proba), 4))

print("\nTaux de prédiction 'Hausse' sur test :", round(np.mean(y_pred == 1), 4))
print("Probabilité moyenne d'une hausse (proba 1) :", round(np.mean(y_proba), 4))
