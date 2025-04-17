import pandas as pd
import ta
import json
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
import joblib

# === 📥 Chargement du dataset ===
def charger_dataset(csv_path="dataset_trades.csv"):
    df = pd.read_csv(csv_path)

    # Vérifie la présence des colonnes nécessaires pour les features
    expected_cols = ["open", "high", "low", "close", "volume", "variation_1h", "variation_24h", "resultat"]
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le dataset : {missing}")

    # Génère les features techniques
    df = generate_technical_features(df)

    # Crée une feature croisement de moyennes mobiles
    df["ma_cross"] = (df["sma_10"] > df["sma_50"]).astype(int)

    # Construit X et y
    features = ["variation_1h", "variation_24h", "volume", "rsi", "ma_cross"]
    X = df[features]
    y = df["resultat"]

    # Sauvegarde le dernier snapshot dans features.json
    save_last_features_snapshot(X)

    return X, y

# === 🧠 Ajout des indicateurs techniques ===
def generate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.sort_index(inplace=True)

    df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()

    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    boll = ta.volatility.BollingerBands(close=df['close'])
    df['bollinger_mavg'] = boll.bollinger_mavg()
    df['bollinger_hband'] = boll.bollinger_hband()
    df['bollinger_lband'] = boll.bollinger_lband()

    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()

    df.dropna(inplace=True)
    return df

# === 💾 Snapshot dans features.json ===
def save_last_features_snapshot(X: pd.DataFrame, path="features.json"):
    try:
        snapshot = X.tail(1).to_dict(orient="records")[0]
        snapshot["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4)
        print(f"✅ Dernières features sauvegardées dans {path}")
    except Exception as e:
        print(f"❌ Erreur sauvegarde features.json : {e}")

# === 📦 Entraînement du modèle ===
def entrainer_model(X, y, model_path="model_bot.pkl"):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    joblib.dump(model, model_path)
    print(f"✅ Modèle entraîné et sauvegardé sous : {model_path}")
    return model

# === 🚀 Script principal ===
if __name__ == "__main__":
    try:
        print("📊 Chargement des données...")
        X, y = charger_dataset()
        print(f"📈 Entraînement sur {len(X)} lignes...")
        entrainer_model(X, y)
    except Exception as e:
        print(f"❌ Erreur durant l'entraînement : {e}")
