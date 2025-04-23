import { useState } from "react";
import axios from "axios";

export default function TradeStopButton({ symbol, mode = "fictif", onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleStop = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await axios.post("http://localhost:5002/vendre_trade", {
        symbol,
        mode
      });

      if (response.data.success) {
        setMessage("✅ Trade stoppé avec succès");
        if (onSuccess) onSuccess();
      } else {
        setMessage("❌ Erreur lors de la vente du trade");
      }
    } catch (err) {
      setMessage("🚨 Erreur serveur : " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <button
        onClick={handleStop}
        disabled={loading}
        className="bg-red-600 hover:bg-red-700 text-white font-semibold py-1 px-4 rounded-xl shadow-md"
      >
        {loading ? "Arrêt..." : `Stopper ${symbol}`}
      </button>
      {message && <p className="text-sm text-zinc-300 italic">{message}</p>}
    </div>
  );
}
