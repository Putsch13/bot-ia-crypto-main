
import ccxt
import pandas as pd

# Connexion à Binance en mode public (pas besoin d'API ici)
exchange = ccxt.binance()

# === Paramètres ===
symbol = "BTC/USDT"
timeframe = "1h"
limit = 500  # Nombre de bougies (max 1000 chez Binance)

# === Récupération des données OHLCV ===
ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

# === Formatage en DataFrame ===
df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# Sauvegarde
df.to_csv("data_binance_btc.csv", index=False)
print("✅ Données récupérées et enregistrées dans data_binance_btc.csv")
