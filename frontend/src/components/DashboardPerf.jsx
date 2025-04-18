import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function DashboardPerf() {
  const [perf, setPerf] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPerf = async () => {
      try {
        const res = await axios.get(`${API_URL}/performance`);
        const data = res.data.data;

        const lastDay = data.gains_by_day?.at(-1)?.gain ?? 0;

        setPerf({
          pnl_total: data.total_gain ?? 0,
          daily_gain: lastDay,
          nb_trades: data.total_trades ?? 0,
          status: "ON", // À rendre dynamique si nécessaire
        });

        setLoading(false);
      } catch (err) {
        console.error("Erreur de perf :", err);
        setLoading(false);
      }
    };

    fetchPerf();
  }, []);

  if (loading || !perf) {
    return <p className="text-zinc-400">Chargement des performances...</p>;
  }

  return (
    <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
      <div>
        <p className="text-sm text-zinc-400">📊 PnL total</p>
        <p className={`text-2xl font-bold ${perf.pnl_total >= 0 ? "text-green-400" : "text-red-400"}`}>
          {perf.pnl_total.toFixed(2)} $
        </p>
      </div>

      <div>
        <p className="text-sm text-zinc-400">💹 Gain du jour</p>
        <p className={`text-2xl font-bold ${perf.daily_gain >= 0 ? "text-green-400" : "text-red-400"}`}>
          {perf.daily_gain.toFixed(2)} $
        </p>
      </div>

      <div>
        <p className="text-sm text-zinc-400">🔁 Total trades</p>
        <p className="text-2xl font-bold text-blue-400">{perf.nb_trades}</p>
      </div>

      <div>
        <p className="text-sm text-zinc-400">⚙️ Statut bot</p>
        <p className={`text-2xl font-bold ${perf.status === "ON" ? "text-green-400" : "text-red-400"}`}>
          {perf.status}
        </p>
      </div>
    </div>
  );
}
