import time
import json
from buzz_tracker import analyze_crypto_sentiment
from twitter_tracker import analyze_crypto_sentiment_twitter

def run_sentiment_collector():
    while True:
        print("\n🔁 Nouvelle collecte de sentiment en cours...")
        try:
            print("📡 Analyse Google News...")
            google_scores = analyze_crypto_sentiment()
            print("✅ Google OK")
            
            print("🐦 Analyse Twitter...")
            twitter_scores = analyze_crypto_sentiment_twitter()
            print("✅ Twitter OK")

            combined = {}
            for coin in set(list(google_scores.keys()) + list(twitter_scores.keys())):
                google = google_scores.get(coin, 0)
                twitter = twitter_scores.get(coin, 0)
                total = round(google + twitter, 3)
                combined[coin] = {
                    "google": google,
                    "twitter": twitter,
                    "total": total
                }

            print("💾 Écriture dans sentiment_scores.json...")
            with open("sentiment_scores.json", "w") as f:
                json.dump(combined, f, indent=4)

            print("✅ Fichier écrit avec succès.")

        except Exception as e:
            print(f"❌ Erreur lors de la collecte : {e}")

        print("⏳ Pause de 10 minutes avant la prochaine collecte...")
        time.sleep(600)  # 10 minutes

if __name__ == "__main__":
    run_sentiment_collector()
