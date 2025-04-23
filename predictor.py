import pandas as pd
from tqdm import tqdm
from datetime import datetime
from ml_brain import get_top_100_symbols, predict_price_movement, charger_modele

def generate_predictions_csv():
    model = charger_modele()
    if model is None:
        print("❌ Modèle introuvable.")
        return

    symbols = get_top_100_symbols()
    predictions = []

    for symbol in tqdm(symbols, desc="🔮 Prédictions IA"):
        try:
            pred, proba = predict_price_movement(symbol)
            predictions.append({
                "symbol": symbol,
                "prediction": pred,
                "proba_up": proba,
                "datetime": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            print(f"❌ Erreur prédiction {symbol} → {e}")

    df = pd.DataFrame(predictions)
    df.to_csv("predictions.csv", index=False)
    print("✅ Fichier predictions.csv généré")
