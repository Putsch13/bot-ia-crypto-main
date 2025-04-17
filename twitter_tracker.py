#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
import certifi
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# 1) Désactiver les avertissements de type InsecureRequestWarning
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# 2) Forcer Python à utiliser le bundle de certificats de certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# Optionnel : si vraiment nécessaire (désactive entièrement la vérification)
# ssl._create_default_https_context = ssl._create_unverified_context

# Après avoir configuré le SSL, on peut importer snscrape
import snscrape.modules.twitter as sntwitter
from textblob import TextBlob
import ccxt

"""
Ce module propose des fonctions pour récupérer et analyser
les tweets relatifs aux cryptomonnaies via snscrape.
"""

# --------------------------------------------------------
# Fonction pour récupérer les 100 cryptos les plus actives de Binance
# --------------------------------------------------------
def get_binance_top_100():
    """
    Récupère les 100 cryptos les plus actives sur Binance avec la paire de trading USDT.
    """
    binance = ccxt.binance()
    markets = binance.load_markets()
    symbols = list(markets.keys())
    # On récupère seulement les cryptos ayant la paire USDT
    spot_symbols = [s.split('/')[0] for s in symbols if '/USDT' in s]
    return list(set(spot_symbols))[:100]

# --------------------------------------------------------
# Fonction pour récupérer les tweets associés à une crypto-monnaie
# --------------------------------------------------------
def get_tweets_for_coin(coin, limit=50):
    """
    Récupère les tweets associés à un coin spécifique (crypto-monnaie).
    
    :param coin: Le nom de la crypto à rechercher sur Twitter (ex. "BTC").
    :param limit: Le nombre maximum de tweets à récupérer.
    :return: Liste de contenu textuel des tweets récupérés.
    """
    # Tu peux ajuster la requête en fonction de tes besoins (langue, date, etc.)
    query = f"{coin} crypto lang:en since:2024-01-01"
    tweets_collected = []
    
    # Parcours des tweets renvoyés par snscrape
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        tweets_collected.append(tweet.content)
    
    return tweets_collected

# --------------------------------------------------------
# Fonction pour analyser le sentiment d'une liste de tweets
# --------------------------------------------------------
def analyze_sentiment(tweets):
    """
    Analyse le sentiment des tweets récupérés en utilisant TextBlob.
    
    :param tweets: Liste de tweets à analyser (chaînes de caractères).
    :return: Score de sentiment moyen (entre -1 et 1).
    """
    sentiments = [TextBlob(t).sentiment.polarity for t in tweets]
    return round(sum(sentiments) / len(sentiments), 3) if sentiments else 0

# --------------------------------------------------------
# Fonction pour analyser le sentiment global des cryptos sur Twitter
# --------------------------------------------------------
def analyze_crypto_sentiment_twitter(coins, limit=50):
    """
    Analyse le sentiment Twitter pour la liste de cryptos `coins`.
    
    :param coins: Liste des cryptos à analyser (ex. ["BTC", "ETH", "BNB", ...]).
    :param limit: Nombre maximum de tweets à récupérer par crypto.
    :return: Un dictionnaire { 'BTC': score, 'ETH': score, ... } avec le score de sentiment.
    """
    results = {}

    for coin in coins:
        print(f"🔍 Analyse de {coin}...")
        tweets = get_tweets_for_coin(coin, limit=limit)
        sentiment_score = analyze_sentiment(tweets)
        results[coin] = sentiment_score

    return results

# --------------------------------------------------------
# Fonction principale (exemple d'utilisation)
# --------------------------------------------------------
if __name__ == "__main__":
    print("🔁 Début de l'analyse des sentiments Twitter pour les cryptos...")

    # Exemple : récupérer la liste des 100 cryptos de Binance
    coins_list = get_binance_top_100()

    # Analyser le sentiment pour ces cryptos
    scores = analyze_crypto_sentiment_twitter(coins_list)

    # Afficher les scores, triés par ordre décroissant
    print("\n📊 Résultats du sentiment Twitter :")
    for coin, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"{coin}: {score}")
