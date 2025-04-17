import React, { useState } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:5002";

export default function StrategyForm() {
  const [form, setForm] = useState({
    montant: 100,
    variation_entree: 1.5,
    objectif_gain: 3,
    seuil_entree: 80,
    seuil_sortie: 40,
    stop_loss: 10,
    reserve: 0,
    mode_execution: "fictif",
    mode_auto: "auto",
    profil: "standard"
  });

  const [status, setStatus] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleStart = async (e) => {
    e.preventDefault();
    setStatus("⏳ Lancement du bot...");
    try {
      const res = await axios.post(`${API_URL}/start_bot`, form);
      setStatus(res.data.status || "✅ Bot lancé !");
    } catch (err) {
      setStatus("❌ Erreur lors du lancement.");
      console.error(err);
    }
  };

  const handleStop = async () => {
    setStatus("⏳ Arrêt du bot...");
    try {
      const res = await axios.post(`${API_URL}/stop_bot`);
      setStatus(res.data.status || "✅ Bot arrêté !");
    } catch (err) {
      setStatus("❌ Erreur lors de l'arrêt.");
      console.error(err);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-md p-5 h-full">
      <h2 className="text-xl font-bold text-gray-800 mb-4">⚙️ Paramètres d’investissement</h2>
      <form onSubmit={handleStart} className="space-y-3 text-sm">

        <div className="grid grid-cols-2 gap-3">
          <input name="montant" type="number" className="input" placeholder="💰 Montant (USDT)" value={form.montant} onChange={handleChange} />
          <input name="objectif_gain" type="number" className="input" placeholder="📈 Objectif gain (%)" value={form.objectif_gain} onChange={handleChange} />
          <input name="stop_loss" type="number" className="input" placeholder="🔻 Stop Loss (%)" value={form.stop_loss} onChange={handleChange} />
          <input name="variation_entree" type="number" className="input" placeholder="📊 Variation min. (%)" value={form.variation_entree} onChange={handleChange} />
          <input name="reserve" type="number" className="input" placeholder="🧷 Réserve sécurité (USDT)" value={form.reserve} onChange={handleChange} />
        </div>

        <div className="grid grid-cols-2 gap-3 mt-2">
          <select name="mode_execution" className="input" value={form.mode_execution} onChange={handleChange}>
            <option value="fictif">🧪 Fictif (simulation)</option>
            <option value="réel">💸 Réel (live Binance)</option>
          </select>

          <select name="mode_auto" className="input" value={form.mode_auto} onChange={handleChange}>
            <option value="auto">♻️ Auto (en continu)</option>
            <option value="manuel">✋ Manuel (1 cycle)</option>
          </select>

          <select name="profil" className="input" value={form.profil} onChange={handleChange}>
            <option value="standard">⚖️ Standard</option>
            <option value="safe">🛡️ Safe</option>
            <option value="risky">🔥 Risky</option>
          </select>

          <input name="seuil_entree" type="number" className="input" placeholder="🔑 Score IA min" value={form.seuil_entree} onChange={handleChange} />
          <input name="seuil_sortie" type="number" className="input" placeholder="🚪 Score IA sortie" value={form.seuil_sortie} onChange={handleChange} />
        </div>

        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-xl hover:bg-blue-700">
          🎯 Démarrer cette stratégie
        </button>

        <button type="button" onClick={handleStop} className="w-full bg-red-600 text-white py-2 rounded-xl hover:bg-red-700 mt-2">
          🛑 Arrêter le Bot
        </button>

        {status && <p className="text-sm mt-2 text-center">{status}</p>}
      </form>
    </div>
  );
}
