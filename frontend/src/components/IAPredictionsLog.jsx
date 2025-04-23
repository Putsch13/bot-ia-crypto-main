import React, { useEffect, useState } from "react";

export default function IAPredictionsLog() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5002/api/predictions")
      .then((res) => res.json())
      .then((data) => {
        setLogs(data.reverse());
      })
      .catch((err) => console.error("Erreur chargement des logs IA:", err));
  }, []);

  return (
    <div className="mt-6 p-4 bg-zinc-900 rounded-2xl shadow-lg">
      <h2 className="text-xl font-semibold mb-4">📊 Journal des prédictions IA (complet)</h2>
      <div className="overflow-auto max-h-[500px]">
        <table className="w-full text-sm text-left text-zinc-300">
          <thead className="text-xs uppercase text-zinc-500 border-b border-zinc-700">
            <tr>
              <th className="py-2 px-4">⏱ Date</th>
              <th className="py-2 px-4">🪙 Symbol</th>
              <th className="py-2 px-4">📊 Score</th>
              <th className="py-2 px-4">🔮 Proba</th>
              <th className="py-2 px-4">🧠 Sentiment</th>
              <th className="py-2 px-4">📈 Var 1h</th>
              <th className="py-2 px-4">📡 Prediction</th>
              <th className="py-2 px-4">🎯 Réel</th>
              <th className="py-2 px-4">💡 Confiance</th>
              <th className="py-2 px-4">✅ Résultat</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((row, idx) => (
              <tr key={idx} className="border-b border-zinc-800">
                <td className="py-1 px-4">{row.Date}</td>
                <td className="py-1 px-4">{row.Symbol}</td>
                <td className="py-1 px-4">{row.Score}</td>
                <td className="py-1 px-4">{row["Probabilité"]}</td>
                <td className="py-1 px-4">{row.Sentiment}</td>
                <td className="py-1 px-4">{row["Variation_1h"]}</td>
                <td className="py-1 px-4">{row.Prediction}</td>
                <td className="py-1 px-4">{row.Real}</td>
                <td className="py-1 px-4">{row.Confidence}</td>
                <td className={`py-1 px-4 font-bold ${row.Result === "SUCCESS" ? "text-green-400" : row.Result === "FAIL" ? "text-red-400" : "text-yellow-400"}`}>
                  {row.Result || "En attente"}
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan="10" className="text-center py-4 text-zinc-500">
                  Aucune prédiction enregistrée.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
