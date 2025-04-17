import pandas as pd

df = pd.read_csv("dataset_trades.csv")

print("\n=== Aperçu du dataset (10 premières lignes) ===\n")
print(df.head(10))
