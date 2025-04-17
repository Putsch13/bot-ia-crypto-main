#!/bin/bash

echo "🔧 Installation du venv..."
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

echo "📦 Installation des packages requis..."
pip install --upgrade pip
pip install snscrape textblob ccxt pandas scikit-learn xgboost flask flask-cors pandas-ta joblib requests

echo "🧠 Téléchargement des corpora TextBlob..."
python -m textblob.download_corpora

echo "✅ Setup terminé ! Tu peux maintenant lancer tes scripts avec :"
echo "source venv/bin/activate && python twitter_tracker.py"
