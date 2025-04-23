import pandas as pd
import numpy as np
import random

# Simuler des données pour 10 cryptos
cryptos = [f"CRYPTO{i}" for i in range(1, 11)]

# Simulations aléatoires mais contrôlées
data = []
for symbol in cryptos:
    variation_score = random.uniform(30, 70)  # variation souvent "moyenne"
    sentiment_score = random.uniform(20, 60)  # Google Trends est souvent pas très haut
    prediction_proba = random.uniform(0.4, 0.6)  # problème courant : modèle peu confiant
    
    # Score final selon la pondération
    score_ia = (
        0.4 * variation_score +
        0.3 * sentiment_score +
        0.3 * prediction_proba * 100  # très important : remise à l’échelle
    )
    
    data.append({
        "Symbole": symbol,
        "Variation Score": round(variation_score, 2),
        "Sentiment Score": round(sentiment_score, 2),
        "Proba Prédiction (%)": round(prediction_proba * 100, 2),
        "Score IA Final": round(score_ia, 2)
    })

df_scores = pd.DataFrame(data)

print(df_scores)

