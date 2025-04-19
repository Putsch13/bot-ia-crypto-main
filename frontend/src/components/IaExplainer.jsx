export default function IaExplainer() {
    return (
      <div className="mt-10 p-6 bg-zinc-800 rounded-xl shadow-lg text-left text-zinc-200 max-w-4xl mx-auto leading-relaxed">
        <h2 className="text-3xl font-bold mb-4 text-white">🤖 IA de Trading - Explication Complète</h2>
  
        <p>
          Notre IA analyse chaque crypto sous plusieurs angles pour fournir une recommandation robuste.
          Voici comment elle fonctionne :
        </p>
  
        <h3 className="text-xl mt-6 font-semibold text-indigo-400">🧮 Analyse Technique</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>RSI (Relative Strength Index)</strong> — mesure si une crypto est surachetée ou survendue.</li>
          <li><strong>Stochastic RSI (stoch_rsi, k, d)</strong> — affine le RSI pour détecter les retournements rapides.</li>
          <li><strong>MACD (Moving Average Convergence Divergence)</strong> — détecte les tendances haussières ou baissières.</li>
          <li><strong>SMA/EMA (Moyennes mobiles)</strong> — identifie la direction générale (sma_10, sma_50, ema_20).</li>
          <li><strong>Bollinger Bands</strong> — mesure la volatilité et les zones de breakout (haut/bas/écart).</li>
          <li><strong>ADX (Average Directional Index)</strong> — mesure la force d’une tendance.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-green-400">📊 Volume & Volatilité</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Volume</strong> — l’intensité des échanges sur la période actuelle.</li>
          <li><strong>volume_ema</strong> — moyenne mobile du volume pour lisser les pics.</li>
          <li><strong>Upper / Lower Shadow</strong> — tailles des mèches (indiquent volatilité et rejets de prix).</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-yellow-400">📈 Mouvements de prix</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Variation 10min / 1h / 24h</strong> — pour capter les dynamiques à court et moyen terme.</li>
          <li><strong>delta_pct</strong> — variation instantanée entre deux bougies.</li>
          <li><strong>variation</strong> — variation globale d’une bougie en %.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-pink-400">📣 Sentiment & Symbolique</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Sentiment Google</strong> — basé sur les tendances de recherche (Google Trends).</li>
          <li><strong>symbol_encoded</strong> — transformation du symbole crypto en valeur numérique pour l’IA.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-cyan-400">⚙️ Mécanisme de Score IA</h3>
        <p className="mt-2">
          Chaque crypto reçoit un score IA sur 100, calculé comme suit :
        </p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>40% Variation</strong> (pondération des mouvements de prix récents)</li>
          <li><strong>30% Sentiment</strong> (popularité sur Google Trends)</li>
          <li><strong>30% Prédiction IA</strong> (sortie du modèle XGBoost)</li>
          <li>Le tout <strong>modulé par la complétude</strong> des données (0 à 1)</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-zinc-300">🚀 Pourquoi notre IA est meilleure ?</h3>
        <p className="mt-2 text-zinc-400">
          Contrairement à des signaux bruts, notre système :
        </p>
        <ul className="list-disc list-inside mt-2 space-y-1 text-zinc-400">
          <li>✔️ Mixe plusieurs horizons temporels</li>
          <li>✔️ Intègre du NLP avec le sentiment</li>
          <li>✔️ Reste pondéré, explicable et transparent</li>
          <li>✔️ Gère les NaN intelligemment avec complétude</li>
        </ul>
  
        <p className="mt-6 text-sm italic text-zinc-400">
          Notre mission : fournir un assistant IA fiable, autonome, mais toujours compréhensible par les humains 💡
        </p>
      </div>
    );
  }
  