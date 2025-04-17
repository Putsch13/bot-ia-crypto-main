from ml_brain import generer_dataset, entrainer_model

if __name__ == "__main__":
    print("🚀 Étape 1 : Génération du dataset...")
    generer_dataset(n_points=50)

    print("\n🧠 Étape 2 : Entraînement du modèle...")
    entrainer_model()

    print("\n✅ Tout est prêt. Le cerveau IA est entraîné et opérationnel.")
