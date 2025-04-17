import React, { useEffect, useState } from "react";
import axios from "axios";

export default function IAReportGPT() {
  const [report, setReport] = useState(null);

  useEffect(() => {
    axios.get("http://localhost:5002/rapport_ia")
      .then(res => setReport(res.data))
      .catch(err => console.error("Erreur /rapport_ia", err));
  }, []);

  if (!report || !report.top || !report.flop) {
    return <div className="text-sm text-gray-500">⏳ Chargement des analyses IA...</div>;
  }

  return (
    <div className="bg-white shadow-md rounded-xl p-6 text-left space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">📊 Rapport IA – Analyse GPT Style</h2>
      <p className="text-gray-700">
        🤖 L'IA a analysé <strong>{report.top.length + report.flop.length}</strong> cryptos en temps réel.
      </p>
      <p className="text-green-600 font-medium">
        ✅ Top performers : {report.top.map(t => t.symbol).join(", ")}
      </p>
      <p className="text-red-500 font-medium">
        ❌ Flop du moment : {report.flop.map(f => f.symbol).join(", ")}
      </p>
      <p className="text-gray-700 italic">
        🧠 Insights : {report.rapport || "aucun insight textuel généré."}
      </p>
    </div>
  );
}
