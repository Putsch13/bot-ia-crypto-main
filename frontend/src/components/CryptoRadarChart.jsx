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

export default function CryptoRadarChart({ symbol }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRadarData = async () => {
      try {
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
  }, [symbol]);

  if (loading) return <p className="text-zinc-400">Chargement du radar...</p>;
  if (error || !data) return <p className="text-red-400">{error || "Erreur inconnue"}</p>;

  return (
    <div className="bg-zinc-900 p-4 rounded-2xl shadow-xl">
      <h2 className="text-lg font-bold text-center text-white mb-4 flex items-center justify-center gap-2">
        🔍 Analyse détaillée IA : {symbol}
        <InfoTooltip text="Analyse des indicateurs techniques avancés pour anticiper les signaux d’achat ou de vente." />
      </h2>

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
