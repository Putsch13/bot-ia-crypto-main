import React, { useEffect, useState } from "react";
import axios from "axios";

const StatsIA = () => {
  const [stats, setStats] = useState({
    mean_proba: null,
    std_proba: null,
    log_loss: null,
    percent_up: null,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5002/api/stats_ia");
        setStats(res.data);
      } catch (err) {
        console.warn("Erreur chargement des stats IA", err);
      }
    };
    fetchStats();
  }, []);

  return (
    <section className="mt-12 p-6 bg-zinc-800 rounded-xl shadow-inner">
      <h2 className="text-2xl font-bold text-white mb-4">📊 Statistiques IA</h2>
      <ul className="text-zinc-300 list-disc pl-5">
        <li>
          Moyenne de probabilité UP : {stats.mean_proba !== null ? stats.mean_proba : "—"}
        </li>
        <li>
          Écart-type de la proba : {stats.std_proba !== null ? stats.std_proba : "—"}
        </li>
        <li>
          Log Loss du modèle : {stats.log_loss !== null ? stats.log_loss : "—"}
        </li>
        <li>
          % de prédictions UP : {stats.percent_up !== null ? `${stats.percent_up}%` : "—"}
        </li>
      </ul>
    </section>
  );
};

export default StatsIA;
