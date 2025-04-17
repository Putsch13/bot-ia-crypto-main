#!/bin/zsh

echo "📦 Activation du venv Python 3.11..."
source venv/bin/activate

echo "🚀 Lancement du serveur Flask sur http://127.0.0.1:5003"
python app.py
