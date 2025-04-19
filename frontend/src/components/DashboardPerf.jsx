import React, { useEffect, useState } from "react";
import axios from "axios";
import IaExplainer from "./IaExplainer";
import CryptoRadarChart from "../components/CryptoRadarChart"; // ou "./..."

const API_URL = "http://127.0.0.1:5002";

export default function DashboardPerf() {
  const [perf, setPerf] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showIAInfo, setShowIAInfo] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [availableCryptos, setAvailableCryptos] = useState([]);
  
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const res = await axios.get(`${API_URL}/rapport_ia`);
        const top = res.data.top || [];
        const flop = res.data.flop || [];
        const all = [...top, ...flop].map((c) => c.symbol);
        setAvailableCryptos(all);
        if (all.length > 0) setSelectedSymbol(all[0]);
      } catch (err) {
        console.error("Erreur chargement des symboles IA :", err);
      }
    };
    
    fetchSymbols();
    
    const fetchPerf = async () => {
      try {
        const res = await axios.get(`${API_URL}/performance`);
        const data = res.data.data;
        const lastDay = data.gains_by_day?.at(-1)?.gain ?? 0;

        setPerf({
          pnl_total: data.total_gain ?? 0,
          daily_gain: lastDay,
          nb_trades: data.total_trades ?? 0,
          status: "ON",
        });

        setLoading(false);
      } catch (err) {
        console.error("Erreur de perf :", err);
        setLoading(false);
      }
    };

    fetchPerf();
  }, []);

  return (
    <>
      <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
        <div>
          <p className="text-sm text-zinc-400">📊 PnL total</p>
          <p className={`text-2xl font-bold ${perf?.pnl_total >= 0 ? "text-green-400" : "text-red-400"}`}>
            {perf?.pnl_total.toFixed(2)} $
          </p>
        </div>
        <div>
          <p className="text-sm text-zinc-400">💹 Gain du jour</p>
          <p className={`text-2xl font-bold ${perf?.daily_gain >= 0 ? "text-green-400" : "text-red-400"}`}>
            {perf?.daily_gain.toFixed(2)} $
          </p>
        </div>
        <div>
          <p className="text-sm text-zinc-400">🔁 Total trades</p>
          <p className="text-2xl font-bold text-blue-400">{perf?.nb_trades}</p>
        </div>
        <div>
          <p className="text-sm text-zinc-400">⚙️ Statut bot</p>
          <p className={`text-2xl font-bold ${perf?.status === "ON" ? "text-green-400" : "text-red-400"}`}>
            {perf?.status}
          </p>
        </div>
      </div>

      {/* 🔘 Bouton + bloc IA */}
      <div className="text-center mt-6">
        <button
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition"
          onClick={() => setShowIAInfo(!showIAInfo)}
        >
          {showIAInfo ? "Masquer les explications IA" : "En savoir plus sur notre IA 🤖"}
        </button>
      </div>

      {showIAInfo && (
        <div className="mt-6">
          <IaExplainer />
        </div>
      )}

      {availableCryptos.length > 0 && (
        <div className="text-center my-6">
          <label className="text-white text-sm mr-2">Voir les indicateurs pour :</label>
          <select
            className="px-4 py-2 rounded-lg text-black"
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
          >
            {availableCryptos.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      )}

      <div className="mt-6 p-4 bg-zinc-900 rounded-2xl shadow-lg">
      <CryptoRadarChart symbol={selectedSymbol} />
      </div>
    </>
  );
}
