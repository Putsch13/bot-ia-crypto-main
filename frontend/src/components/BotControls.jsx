import React, { useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function BotControls() {
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const triggerAuditIA = async () => {
    try {
      setStatus("🧠 Lancement de l’audit IA...");
      setLoading(true);
      await axios.get(`${API_URL}/analyser_sentiment`);
      setStatus("✅ Audit IA terminé. Rapport mis à jour.");
    } catch (err) {
      console.error("Erreur audit IA", err);
      setStatus("❌ Échec de l’audit IA.");
    } finally {
      setLoading(false);
    }
  };

  const startAutoBot = async () => {
    try {
      setStatus("🚀 Démarrage du bot IA...");
      setLoading(true);
      const res = await axios.post(`${API_URL}/start_bot`);
      setStatus(res.data.status || "✅ Bot IA démarré !");
    } catch (err) {
      console.error("Erreur start bot", err);
      setStatus("❌ Échec du démarrage.");
    } finally {
      setLoading(false);
    }
  };

  const stopBot = async () => {
    try {
      setStatus("🛑 Arrêt du bot...");
      setLoading(true);
      const res = await axios.post(`${API_URL}/stop_bot`);
      setStatus(res.data.status || "✅ Bot arrêté !");
    } catch (err) {
      console.error("Erreur stop bot", err);
      setStatus("❌ Erreur à l'arrêt.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">🎮 Contrôle IA & Bot</h2>

      <div className="space-y-3">
        <button
          onClick={triggerAuditIA}
          disabled={loading}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-xl text-sm"
        >
          🧠 Lancer l’audit IA
        </button>

        <button
          onClick={startAutoBot}
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-xl text-sm"
        >
          🚀 Démarrer le Bot IA
        </button>

        <button
          onClick={stopBot}
          disabled={loading}
          className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded-xl text-sm"
        >
          🛑 Stopper le Bot IA
        </button>
      </div>

      {status && <p className="text-sm mt-4 text-center text-gray-700">{status}</p>}
    </div>
  );
}
