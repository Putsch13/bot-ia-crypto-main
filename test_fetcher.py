print("✅ test_fetcher.py lancé")  # Vérifie que le script se lance bien

try:
    from data_fetcher import get_all_variations
    print("📦 Import réussi ✅")
except Exception as e:
    print(f"❌ Erreur d'import : {e}")

try:
    # Test avec 2 cryptos pour aller plus vite
    results = get_all_variations(limit=2)
    print("📊 Récupération des variations réussie ✅")
except Exception as e:
    print(f"❌ Erreur dans get_all_variations : {e}")
    results = {}

# Affichage
for symbol, variations in results.items():
    print(f"\n🪙 {symbol}")
    for timeframe, change in variations.items():
        print(f"  {timeframe}: {change}")
