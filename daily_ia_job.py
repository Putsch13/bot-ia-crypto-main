from predict_live import run_predict_live
from datetime import datetime

def run_daily():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] 🔁 Lancement de la prédiction IA quotidienne...")
    result = run_predict_live(mode="fictif")
    print(f"[{now}] ✅ Résultat IA : {result}")

if __name__ == "__main__":
    run_daily()
