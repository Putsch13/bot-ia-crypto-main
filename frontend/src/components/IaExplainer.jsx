export default function IaExplainer() {
    return (
      <div className="mt-10 p-6 bg-zinc-800 rounded-xl shadow-lg text-left text-zinc-200 max-w-4xl mx-auto leading-relaxed">
        <h2 className="text-3xl font-bold mb-4 text-white">🤖 IA de Trading - Explication Complète</h2>
  
        <p>
          Notre IA analyse chaque crypto sous plusieurs angles pour fournir une recommandation robuste et transparente.
          Voici tout ce qui entre en jeu dans le cerveau du bot :
        </p>
  
        <h3 className="text-xl mt-6 font-semibold text-indigo-400">🧮 Analyse Technique</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>RSI</strong> — détecte les zones de surachat/survente.</li>
          <li><strong>Stochastic RSI</strong> — affine le RSI pour détecter les retournements rapides (<code>stoch_rsi</code>, <code>k</code>, <code>d</code>).</li>
          <li><strong>MACD</strong> — suit la tendance avec <code>macd</code>, <code>macd_signal</code>, <code>macd_diff</code>, <code>macd_cross</code>.</li>
          <li><strong>Moyennes mobiles</strong> — <code>sma_10</code>, <code>sma_50</code>, <code>ema_20</code> pour capter la direction générale.</li>
          <li><strong>Bollinger Bands</strong> — mesure la volatilité avec <code>bollinger_high</code>, <code>low</code>, <code>width</code>.</li>
          <li><strong>ADX</strong> — mesure la force d'une tendance.</li>
          <li><strong>Autres oscillateurs</strong> — <code>williams_r</code>, <code>roc</code>, <code>mom</code>, <code>ult_osc</code>, <code>cci</code>.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-green-400">📊 Volume & Volatilité</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Volume brut</strong> — <code>volume</code>, <code>volume_ema</code> (lissé).</li>
          <li><strong>ATR</strong> — volatilité moyenne réelle.</li>
          <li><strong>Bougies japonaises</strong> — <code>upper_shadow</code>, <code>lower_shadow</code>, <code>body_size</code>.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-yellow-400">📈 Mouvements de prix</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Variations temporelles</strong> — <code>variation_10min</code>, <code>1h</code>, <code>24h</code>.</li>
          <li><strong>delta_pct</strong> — variation instantanée entre deux bougies.</li>
          <li><strong>variation</strong> — variation totale d’une bougie.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-pink-400">📣 Sentiment & Symbolique</h3>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>Sentiment Google</strong> — score basé sur Google Trends.</li>
          <li><strong>symbol_encoded</strong> — encodage numérique de la crypto pour le modèle.</li>
          <li><strong>rsi_overbought / oversold</strong> — flags pour simplifier les signaux RSI.</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-cyan-400">⚙️ Mécanisme de Score IA</h3>
        <p className="mt-2">
          Chaque crypto reçoit un <strong>score IA sur 100</strong>, calculé ainsi :
        </p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>40%</strong> ➜ Variations récentes (<code>variation_*</code>)</li>
          <li><strong>30%</strong> ➜ Sentiment social (<code>sentiment</code>)</li>
          <li><strong>30%</strong> ➜ Prédiction IA (<code>XGBoost.predict_proba()</code>)</li>
          <li>Le tout <strong>ajusté par la complétude</strong> des données (0 à 1)</li>
        </ul>
  
        <h3 className="text-xl mt-6 font-semibold text-zinc-300">🚀 Pourquoi notre IA est différente</h3>
        <p className="mt-2 text-zinc-400">
          Contrairement à des signaux bruts, notre système :
        </p>
        <ul className="list-disc list-inside mt-2 space-y-1 text-zinc-400">
          <li>✔️ Croise plusieurs horizons temporels</li>
          <li>✔️ Intègre du NLP (analyse du sentiment)</li>
          <li>✔️ Est pondéré, interprétable et transparent</li>
          <li>✔️ Gère les NaN intelligemment</li>
          <li>✔️ S'adapte au profil de risque utilisateur</li>
        </ul>
  
        <p className="mt-6 text-sm italic text-zinc-400">
          Notre mission : fournir un assistant IA fiable, autonome, mais toujours compréhensible par les humains 💡
        </p>
      </div>
    );
  }
  