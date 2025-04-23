from ml_brain import generer_dataset, entrainer_model
from predictor import generate_predictions_csv
import time

while True:
    print("🚀 Lancement du cycle complet IA...\n")
    generer_dataset()
    entrainer_model()
    generate_predictions_csv()
    print("✅ Cycle terminé. Attente avant prochain lancement...\n")
    time.sleep(300)
