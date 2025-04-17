import json
import os

def charger_portefeuille(mode):
    with open("config/portefeuille.json", "r") as f:
        data = json.load(f)
    return data.get(mode, {})

def sauvegarder_portefeuille(nouveau_portefeuille, mode):
    with open("config/portefeuille.json", "r") as f:
        data = json.load(f)
    data[mode] = nouveau_portefeuille
    with open("config/portefeuille.json", "w") as f:
        json.dump(data, f, indent=4)

CONFIG_PATH = "config/config.json"
PORTFOLIO_PATH = "config/portefeuille.json"

# Valeurs par défaut
default_config = {
    "capital_total": 1000.0,
    "mode": "automatique",  # automatique | unique | automatique_composé
    "seuil_entree": 0.03,
    "seuil_sortie_perte": -0.02,
    "seuil_sortie_gain": 0.05
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(default_config)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def load_portfolio():
    if not os.path.exists(PORTFOLIO_PATH):
        save_portfolio({})
    with open(PORTFOLIO_PATH, "r") as f:
        return json.load(f)

def save_portfolio(portfolio):
    os.makedirs(os.path.dirname(PORTFOLIO_PATH), exist_ok=True)
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(portfolio, f, indent=4)
