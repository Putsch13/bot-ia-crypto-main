import pandas as pd

df = pd.read_csv("dataset_enrichi.csv")
print("\n📊 Colonnes du dataset enrichi :\n")
print(df.columns.tolist())
