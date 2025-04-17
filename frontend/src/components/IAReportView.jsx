import React, { useEffect, useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function IAReportView() {
  const [rapport, setRapport] = useState("");
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState(false);

  const fetchRapport = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/rapport_ia`);
      if (res.data.rapport && typeof res.data.rapport === "string") {
        setRapport(res.data.rapport);
        setErreur(false);
      } else {
        setErreur(true);
      }
    } catch (err) {
      console.error("Erreur chargement rapport IA", err);
      setErreur(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRapport();
  }, []);

  return (
    <div className="bg-white p-5 rounded-2xl shadow-md h-full overflow-auto">
      <h2 className="text-xl font-bold text-gray-800 mb-4">🧾 Rapport IA global</h2>

      {loading ? (
        <p className="text-sm text-gray-500">⏳ Chargement du rapport IA...</p>
      ) : erreur ? (
        <p className="text-sm text-red-500">❌ Erreur lors du chargement du rapport.</p>
      ) : (
        <pre className="text-sm whitespace-pre-wrap text-gray-800">{rapport}</pre>
      )}

      <button
        onClick={fetchRapport}
        className="mt-4 text-sm text-blue-500 hover:underline"
      >
        🔄 Rafraîchir
      </button>
    </div>
  );
}
