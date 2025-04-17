import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function LogPanel() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await axios.get(`${API_URL}/logs`);
        setLogs(res.data.trades || []);
      } catch (err) {
        console.error("Erreur chargement logs :", err);
      }
    };
    fetchLogs();
  }, []);

  if (!logs.length) return <p className="text-zinc-400">Aucun trade trouvé...</p>;

  return (
    <div className="overflow-x-auto text-sm">
      <table className="min-w-full table-auto border-collapse border border-zinc-700">
        <thead className="bg-zinc-800 text-zinc-300">
          <tr>
            <th className="px-4 py-2 border">Date</th>
            <th className="px-4 py-2 border">Symbole</th>
            <th className="px-4 py-2 border">Action</th>
            <th className="px-4 py-2 border">Prix</th>
            <th className="px-4 py-2 border">Quantité</th>
            <th className="px-4 py-2 border">Gain (%)</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((trade, idx) => (
            <tr key={idx} className="text-white hover:bg-zinc-800">
              <td className="px-4 py-2 border">{trade.Date}</td>
              <td className="px-4 py-2 border">{trade.Symbol}</td>
              <td className="px-4 py-2 border">{trade.Action}</td>
              <td className="px-4 py-2 border">{parseFloat(trade.Price).toFixed(2)} $</td>
              <td className="px-4 py-2 border">{trade.Quantity}</td>
              <td className={`px-4 py-2 border font-semibold ${parseFloat(trade["Gain (%)"].replace("%", "")) >= 0 ? "text-green-400" : "text-red-400"}`}>
                {trade["Gain (%)"]}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
