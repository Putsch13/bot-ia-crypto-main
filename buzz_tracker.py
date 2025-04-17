# buzz_tracker.py
import requests

API_KEY = "56758c3c1169ce340c6fc07baf30196e"  # va sur https://gnews.io/

def analyze_crypto_sentiment_google(coins):
    result = {}
    for symbol in coins:
        try:
            url = f"https://gnews.io/api/v4/search?q={symbol}&lang=en&token={API_KEY}"
            res = requests.get(url)
            articles = res.json().get("articles", [])
            score = 0
            for a in articles:
                title = a["title"].lower()
                if any(w in title for w in ["surge", "rally", "adoption", "breakout"]):
                    score += 1
                elif any(w in title for w in ["crash", "ban", "decline", "sell-off"]):
                    score -= 1
            final = round((score / max(1, len(articles)) + 1) / 2, 2)  # Normalisé
            result[symbol.upper()] = final
        except:
            result[symbol.upper()] = 0.5
    return result

def get_google_sentiment_score(symbol):
    """Retourne un score unique de sentiment entre 0 et 1 pour 1 crypto"""
    result = analyze_crypto_sentiment_google([symbol])
    return result.get(symbol.upper(), 0.5)
