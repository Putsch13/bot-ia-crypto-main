# model.py

# Importation des fonctions nécessaires pour charger le modèle et effectuer la prédiction
from sklearn.ensemble import RandomForestClassifier
import pickle

def charger_modele():
    try:
        with open('model_bot.pkl', 'rb') as file:
            model = pickle.load(file)
        return model
    except Exception as e:
        print(f"Erreur lors du chargement du modèle : {e}")
        return None

def prediction_model(model, variation_1h, variation_24h, volume, market_cap, ma_cross):
    try:
        features = [
            variation_1h,
            variation_24h,
            volume,
            market_cap,
            ma_cross
        ]
        return model.predict([features])[0]
    except Exception as e:
        print(f"Erreur lors de la prédiction : {e}")
        return None

def charger_et_predire(symbol, vars, model):
    ma_cross = 1 if (vars['variation_1h'] or 0) > (vars['variation_10min'] or 0) else 0
    pred = prediction_model(model, vars['variation_1h'], vars['variation_24h'], 1_000_000, 50, ma_cross)
    pred_score = 1 if pred == 1 else 0
    return pred_score
