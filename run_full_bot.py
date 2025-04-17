from audit_cryptos import run_full_audit
from predict_live import run_predict_live

if __name__ == "__main__":
    print("🚀 Lancement de l'audit complet des cryptos...")
    top5, flop5, summary = run_full_audit()
    
    print("\n🧠 Résumé de l'audit IA :")
    print(summary)

    print("\n📊 Lancement du moteur de prédiction en mode fictif...")
    result = run_predict_live(mode="fictif")

    print("\n✅ Résultat de l'exécution du bot :")
    print(result)
