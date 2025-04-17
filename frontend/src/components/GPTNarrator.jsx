import React, { useEffect, useState } from "react";
import axios from "axios";

export default function GPTNarrator() {
  const [report, setReport] = useState(null);

  useEffect(() => {
    axios.get("http://localhost:5002/rapport_ia")
      .then(res => setReport(res.data))
      .catch(err => console.error("Erreur rapport IA :", err));
  }, []);

  if (!report || !report.top || !report.flop) {
    return (
      <p className="text-sm text-zinc-400 italic">
        Chargement du rapport analytique IA...
      </p>
    );
  }

  const top = report.top[0];
  const flop = report.flop[0];
  const total = report.top.length + report.flop.length;
  const sentimentGlobal = Math.round((top.sentiment ?? 0.5) * 100);

  return (
    <div className="space-y-5 text-left leading-relaxed text-zinc-100 text-sm">
      <p className="text-base text-zinc-200 font-medium">
        📊 <strong>Note analytique – Synthèse des données IA</strong>
      </p>

      <p>
        Le système d’analyse algorithmique a traité un total de <strong>{total}</strong> crypto-actifs au cours de la dernière session.
        L’évaluation repose sur une pondération équilibrée entre les variations de prix à court et moyen terme, les signaux techniques, le sentiment de marché, ainsi que la prédiction IA issue du modèle de classification.
      </p>

      <p>
        À ce jour, l’actif <span className="text-green-400 font-semibold">{top.symbol}</span> se distingue par un score consolidé de <strong>{top.score_ia}</strong>, reflétant à la fois une dynamique de marché favorable et une prédiction IA haussière.
        Ce positionnement peut être attribué à une combinaison de variation positive sur 1h/24h, un volume significatif et un sentiment de marché supérieur à la moyenne ({sentimentGlobal}%).
      </p>

      <p>
        À l’inverse, <span className="text-red-400 font-semibold">{flop.symbol}</span> présente les indicateurs les moins favorables. Le score IA de <strong>{flop.score_ia}</strong> suggère un potentiel de baisse, appuyé par des performances techniques faibles et un sentiment global dégradé.
      </p>

      <p>
        Dans l’ensemble, le marché affiche un biais neutre à légèrement positif, avec une moyenne sentimentale autour de <strong>{sentimentGlobal}%</strong>. Ce climat pourrait favoriser les prises de position sélectives à court terme.
      </p>

      <p className="text-zinc-400 italic">
        📌 Cette synthèse est générée automatiquement par le moteur IA du bot. Elle ne constitue pas un conseil en investissement, mais une lecture algorithmique du marché crypto en temps réel.
      </p>
    </div>
  );
}
