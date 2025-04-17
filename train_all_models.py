import os
from ai_engine import train_model

# Dossiers
data_dir = "data_multi_tf"
models_dir = "models"
os.makedirs(models_dir, exist_ok=True)

# Récupération de tous les fichiers CSV dans data_multi_tf
csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]

results = []

# Entraînement de tous les modèles
for file in csv_files:
    symbol_tf = file.replace(".csv", "")  # ex: BTCUSDT_15m
    csv_path = os.path.join(data_dir, file)
    model_path = os.path.join(models_dir, f"xgb_{symbol_tf}.model")
    try:
        _, acc = train_model(csv_path, model_path)
        results.append((symbol_tf, "✅", round(acc, 4)))
    except Exception as e:
        results.append((symbol_tf, "❌", str(e)))

# Résumé
print("\n🧠 Résultat de l'entraînement IA :")
for res in results:
    print(f"{res[0]} → {res[1]} ({res[2]})")
