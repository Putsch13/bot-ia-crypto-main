import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import InfoTooltip from "./InfoTooltip";

export default function CryptoRadarChart({ symbol, intervalle }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRadarData = async () => {
      try {
        // Vérifie si l'intervalle est inférieur à 2 minutes
        if (intervalle < 2) {
          alert("⚠️ L’intervalle minimum autorisé est de 2 minutes.");
          setError("Intervalle trop court.");
          setLoading(false);
          return;
        }

        const res = await axios.get(`http://127.0.0.1:5002/radar_data?symbol=${symbol}`);
        console.log("✅ Données radar reçues :", res.data);

        const radar = res.data.features;
        if (!radar) throw new Error("Aucune feature trouvée");

        setData(
          Object.entries(radar).map(([key, value]) => ({
            feature: key,
            value,
          }))
        );
      } catch (err) {
        console.error("❌ Erreur radar :", err);
        setError("Erreur chargement des données IA");
      } finally {
        setLoading(false);
      }
    };

    fetchRadarData();
  }, [symbol, intervalle]);

  if (loading) return <p className="text-zinc-400">Chargement du radar...</p>;
  if (error || !data) return <p className="text-red-400">{error || "Erreur inconnue"}</p>;

  return (
    <div className="bg-zinc-900 p-4 rounded-2xl shadow-xl">
      <h2 className="text-lg font-bold text-center text-white mb-4">
        🔍 Analyse détaillée IA : {symbol}
      </h2>

      <div className="mb-2 flex items-center gap-2">
        <label className="text-sm text-white flex items-center gap-1">
          Intervalle (min)
          <InfoTooltip text="Délai entre deux audits IA. Minimum recommandé : 2 minutes pour éviter les surcharges." />
        </label>
        <span className="text-sm text-zinc-400">{intervalle} min</span>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="#444" />
          <PolarAngleAxis dataKey="feature" stroke="#ccc" />
          <PolarRadiusAxis stroke="#777" />
          <Radar
            name="IA Score"
            dataKey="value"
            stroke="#00f5d4"
            fill="#00f5d4"
            fillOpacity={0.6}
          />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
