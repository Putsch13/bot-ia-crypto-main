import ccxt
import pandas as pd
from data_fetcher import fetch_enriched_features

exchange = ccxt.binance()
dataset = []

def get_valid_usdt_symbols(limit=100):
    markets = exchange.load_markets()
    pairs = [
        s for s in markets
        if s.endswith("/USDT") and ":" not in s and not s.startswith("USD")
    ]
    return pairs[:limit]

symbols = get_valid_usdt_symbols()

for symbol in symbols:
    try:
        print(f"🔍 Traitement {symbol}...")
        df = fetch_enriched_features(symbol)
        if df is not None and not df.empty:
            print(f"✅ {symbol} → OK")
            last_row = df.iloc[-1].copy()
            last_row["symbol"] = symbol
            dataset.append(last_row)

        else:
            print(f"⚠️ {symbol} → DF vide ou None")
    except Exception as e:
        print(f"❌ {symbol} ignoré : {e}")
        continue

# Sauvegarde du dataset
if dataset:
    df_final = pd.DataFrame(dataset)
    df_final.to_csv("dataset_enrichi.csv", index=False)
    print(f"\n✅ Fichier dataset_enrichi.csv généré avec {len(df_final)} cryptos.")
else:
    print("❌ Aucun snapshot enregistré.")
