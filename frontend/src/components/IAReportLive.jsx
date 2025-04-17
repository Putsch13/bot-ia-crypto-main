import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function IAReportLive() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLive = async () => {
    try {
      const res = await axios.get(`${API_URL}/rapport_ia`);
      const top = res.data?.top || [];
      const flop = res.data?.flop || [];
      setData([...top, ...flop]); // pour avoir les deux en live
    } catch (err) {
      console.error("Erreur chargement IA Live", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLive();
    const interval = setInterval(fetchLive, 60000); // refresh toutes les 60s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-md p-5 text-sm text-gray-600 italic">
        🧠 Chargement des analyses IA en cours...
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-5">
      <h2 className="text-xl font-bold text-gray-800 mb-3">📊 Analyse IA en temps réel</h2>

      <div className="max-h-96 overflow-y-auto space-y-3 text-sm text-gray-700">
        {data.map((crypto, idx) => (
          <div key={idx} className="p-3 bg-gray-50 rounded-xl border">
            <p className="font-semibold text-gray-800">{crypto.symbol}</p>
            <p>
              La crypto <strong>{crypto.symbol}</strong> présente actuellement une variation de{" "}
              {crypto.variation_10min ?? "?"}% sur 10 minutes, avec un score IA estimé à{" "}
              <strong>{crypto.score_ia}</strong>.{" "}
              Le sentiment détecté est de <strong>{(crypto.sentiment * 100).toFixed(1)}%</strong>.{" "}
              L’IA anticipe une{" "}
              <span className={crypto.score_ia > 50 ? "text-green-600 font-bold" : "text-red-600 font-bold"}>
                {crypto.score_ia > 50 ? "hausse" : "baisse"} probable
              </span>{" "}
              à court terme.
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
