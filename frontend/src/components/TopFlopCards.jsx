import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function TopFlopCards() {
  const [top, setTop] = useState([]);
  const [flop, setFlop] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API_URL}/rapport_ia`);
        if (res.data) {
          setTop(res.data.top || []);
          setFlop(res.data.flop || []);
        }
      } catch (err) {
        console.error("Erreur chargement top/flop IA :", err);
      }
    };
    fetchData();
  }, []);

  const Card = ({ crypto, index, type }) => {
    const color = type === "top" ? "green" : "red";
    return (
      <div className={`border rounded-2xl p-4 shadow-md bg-white`}>
        <h3 className="text-lg font-semibold text-gray-800 flex justify-between">
          <span>{index + 1}. {crypto.symbol}</span>
          <span className={`text-${color}-600 font-bold`}>{crypto.score_ia}</span>
        </h3>
        <div className="text-xs text-gray-500 mt-1">
          Variation 10m : {crypto.variation_10min ?? "?"}%<br />
          Sentiment : {(crypto.sentiment * 100).toFixed(1)}%
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h2 className="text-xl font-bold text-green-700 mb-2">🚀 Top 5 Cryptos IA</h2>
        <div className="grid gap-3">
          {top.length === 0 ? (
            <p className="text-sm text-gray-500 italic">Aucune donnée pour l’instant.</p>
          ) : (
            top.map((c, i) => <Card key={i} crypto={c} index={i} type="top" />)
          )}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-red-600 mb-2">🛑 Flop 5 Cryptos IA</h2>
        <div className="grid gap-3">
          {flop.length === 0 ? (
            <p className="text-sm text-gray-500 italic">Aucune donnée pour l’instant.</p>
          ) : (
            flop.map((c, i) => <Card key={i} crypto={c} index={i} type="flop" />)
          )}
        </div>
      </div>
    </div>
  );
}
