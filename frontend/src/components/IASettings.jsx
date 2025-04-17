import React, { useState, useEffect } from "react";
import axios from "axios";
import { startBot } from "../api";

const API_URL = "http://127.0.0.1:5002";

const IASettings = () => {
  const [config, setConfig] = useState(null);
  const [mode, setMode] = useState("fictif");
  const [profil, setProfil] = useState("moyen");
  const [capital, setCapital] = useState(1000);
  const [takeProfit, setTakeProfit] = useState(5);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await axios.get(`${API_URL}/get_config`);
        setConfig(res.data);
      } catch (err) {
        console.error("Erreur de chargement config", err);
        setStatus({ type: "error", message: "Échec du chargement." });
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async () => {
    try {
      await axios.post(`${API_URL}/set_config`, config);
      setStatus({ type: "success", message: "Configuration sauvegardée ✅" });
    } catch (err) {
      setStatus({ type: "error", message: "Erreur lors de la sauvegarde ❌" });
    }
  };

  const lancerBot = async () => {
    const params = {
      montant: capital,
      variation_entree: 1.5,  // à remplacer par champ si besoin
      objectif_gain: takeProfit,
      mode_execution: mode,
      mode_auto: "auto",
      seuil_entree: config.seuil_ia,
      seuil_sortie: 30,
      stop_loss: 10,
      reserve: 0,
      profil: profil
    };    

    try {
      const res = await startBot(params);
      console.log("✅ Bot lancé depuis le front :", res);
      setStatus({ type: "success", message: res.status || "Bot lancé." });
    } catch (err) {
      console.error("❌ Erreur lancement bot :", err);
      setStatus({ type: "error", message: "Erreur lancement bot ❌" });
    }
  };
    
  if (loading) return <p className="text-gray-400">Chargement de la configuration...</p>;

  if (!config) return <p className="text-red-400">⚠️ Impossible de charger la config.</p>;

  return (
    <div className="p-4 bg-zinc-900 rounded-2xl shadow-lg space-y-4 text-sm text-white">
      <h2 className="text-xl font-bold mb-2">🎛️ Configuration IA</h2>

      {/* Mode de trading */}
      <div>
        <label className="block mb-1">Mode de trading</label>
        <select
          className="w-full p-2 rounded bg-zinc-800 text-white"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="fictif">Fictif (simulation)</option>
          <option value="reel">Réel (Binance)</option>
        </select>
      </div>

      {/* Profil */}
      <div>
        <label className="block mb-1">Profil</label>
        <select
          className="w-full p-2 rounded bg-zinc-800 text-white"
          value={profil}
          onChange={(e) => setProfil(e.target.value)}
        >
          <option value="prudent">Prudent</option>
          <option value="moyen">Moyen</option>
          <option value="risque">Risqué</option>
        </select>
      </div>

      {/* Capital */}
      <div>
        <label className="block mb-1">Capital ($)</label>
        <input
          type="number"
          value={capital}
          onChange={(e) => setCapital(Number(e.target.value))}
          className="w-full p-2 rounded bg-zinc-800 text-white"
        />
      </div>

      {/* Take profit */}
      <div>
        <label className="block mb-1">Take Profit (%)</label>
        <input
          type="number"
          value={takeProfit}
          onChange={(e) => setTakeProfit(Number(e.target.value))}
          className="w-full p-2 rounded bg-zinc-800 text-white"
        />
      </div>

      <hr className="border-zinc-700 my-4" />

      {/* Seuil IA */}
      <div>
        <label className="block mb-1">Seuil IA (%)</label>
        <input
          type="number"
          name="seuil_ia"
          value={config.seuil_ia || ""}
          onChange={handleChange}
          className="w-full p-2 rounded bg-zinc-800 text-white"
        />
      </div>

      {/* Mode investissement */}
      <div>
        <label className="block mb-1">Mode d’investissement</label>
        <select
          name="mode_invest"
          value={config.mode_invest || "unique"}
          onChange={handleChange}
          className="w-full p-2 rounded bg-zinc-800 text-white"
        >
          <option value="unique">Unique</option>
          <option value="automatique">Automatique</option>
          <option value="automatique_composé">Automatique Composé</option>
        </select>
      </div>

      {/* Intervalle */}
      <div>
        <label className="block mb-1">Intervalle (minutes)</label>
        <input
          type="number"
          name="intervalle_minutes"
          value={config.intervalle_minutes || ""}
          onChange={handleChange}
          className="w-full p-2 rounded bg-zinc-800 text-white"
        />
      </div>

      {/* Boutons */}
      <div className="flex flex-col gap-2 pt-4">
        <button
          className="bg-emerald-600 hover:bg-emerald-700 text-white p-2 rounded"
          onClick={lancerBot}
        >
          🚀 Lancer le Bot IA
        </button>

        <button
          className="bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded"
          onClick={handleSubmit}
        >
          💾 Enregistrer la Config
        </button>
      </div>

      {status && (
        <p className={`mt-2 ${status.type === "success" ? "text-green-400" : "text-red-400"}`}>
          {status.message}
        </p>
      )}
    </div>
  );
};

export default IASettings;
