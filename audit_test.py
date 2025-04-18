import logging
from ml_brain import enrichir_features, encoder_symbols, charger_et_predire_from_df, charger_modele
from audit_cryptos import get_ohlcv_df, get_sentiment_scores_dynamic, FEATURE_COLUMNS
import pandas as pd

# === LOGGER SETUP ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# === TEST SYMBOL ===
symbol = "BTCUSDT"
logger.info(f"🧪 Test audit pour {symbol}")

# 1. Charger le modèle
model = charger_modele()
if not model:
    logger.error("❌ Modèle non chargé.")
    exit()

# 2. Charger données OHLCV
df = get_ohlcv_df(symbol)
if df is None or df.empty:
    logger.error("❌ OHLCV DataFrame vide.")
    exit()
logger.info(f"✅ Données OHLCV : {df.shape}")

# 3. Enrichir les features
df = enrichir_features(df)
logger.info(f"✅ Features enrichies : {df.columns.tolist()}")

# 4. Ajouter colonne symbol
df["symbol"] = symbol

# 5. Encoder le symbole
try:
    df, _ = encoder_symbols(df)
    assert "symbol_encoded" in df.columns, "❌ symbol_encoded manquant après encodage"
except Exception as e:
    logger.error(f"❌ encoder_symbols a échoué : {e}")
    exit()

# 6. Ajouter sentiment
sentiments = get_sentiment_scores_dynamic([symbol])
coin = symbol.replace("USDT", "")
sentiment = sentiments.get(coin, {}).get("total", 0.5)
df["sentiment"] = sentiment

# 7. Vérif colonnes
missing_cols = [col for col in FEATURE_COLUMNS if col not in df.columns]
if missing_cols:
    logger.error(f"❌ Colonnes manquantes : {missing_cols}")
    exit()

# 8. Complétude
df["completeness"] = df[FEATURE_COLUMNS].notna().mean(axis=1)

# 9. Prédiction
try:
    pred_score = charger_et_predire_from_df(df)
    logger.info(f"✅ Prédiction OK → {pred_score}")
except Exception as e:
    logger.error(f"❌ Échec prédiction : {e}")
    exit()

# 10. Résumé
latest = df.iloc[-1]
print("\n🎯 Résumé :")
for col in FEATURE_COLUMNS:
    print(f"{col}: {latest[col]}")
print(f"[DEBUG] Type de pred_score : {type(pred_score)}")
print(pred_score.tail())
print(f"✅ Sentiment: {sentiment:.2f}")
# Si pred_score est une DataFrame avec une colonne "prediction", on extrait la dernière valeur
if isinstance(pred_score, pd.DataFrame) and "prediction" in pred_score.columns:
    pred = int(pred_score["prediction"].iloc[-1])
else:
    pred = int(pred_score)  # sinon, on suppose que c’est déjà un int ou un float

print(f"✅ IA Prédiction: {'Hausse' if pred == 1 else 'Baisse'}")
