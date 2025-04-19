import React, { useEffect, useState } from "react";
import InfoTooltip from "./InfoTooltip";

const ActiveTradesPanel = () => {
  const [portfolio, setPortfolio] = useState({ fictif: {}, reel: {} });
  const [livePrices, setLivePrices] = useState({});

  // Récupère le portefeuille toutes les 5s
  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const res = await fetch("http://localhost:5002/get_portfolio");
        const data = await res.json();
        setPortfolio(data);
      } catch (err) {
        console.error("Erreur de chargement du portefeuille :", err);
      }
    };

    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 5000);
    return () => clearInterval(interval);
  }, []);

  // Récupère les prix en temps réel depuis Binance toutes les 10s
  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const res = await fetch("https://api.binance.com/api/v3/ticker/price");
        const data = await res.json();
        const prices = {};
        data.forEach((item) => {
          prices[item.symbol] = parseFloat(item.price);
        });
        setLivePrices(prices);
      } catch (err) {
        console.error("Erreur récupération prix :", err);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 10000);
    return () => clearInterval(interval);
  }, []);

  // Stopper un trade côté backend
  const stopTrade = async (symbol, mode) => {
    try {
      const res = await fetch("http://localhost:5002/stop_trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, mode }),
      });
      const result = await res.json();
      console.log(result);

      const refreshed = await fetch("http://localhost:5002/get_portfolio");
      setPortfolio(await refreshed.json());
    } catch (err) {
      console.error("Erreur suppression trade :", err);
    }
  };

  // Génère le tableau des trades par mode
  const renderTrades = (mode) => {
    const trades = portfolio[mode];
    if (!trades || Object.keys(trades).length === 0) {
      return <p className="text-gray-500 italic">Aucun trade actif.</p>;
    }

    return (
      <table className="w-full text-sm text-white mt-2">
        <thead>
          <tr className="text-zinc-400 border-b border-zinc-700">
            <th>
              Symbol
              <InfoTooltip text="Paire de trading utilisée (ex: BTCUSDT)." />
            </th>
            <th>
              Prix d’achat
              <InfoTooltip text="Prix auquel la position a été ouverte." />
            </th>
            <th>
              Montant $
              <InfoTooltip text="Montant investi en dollars sur ce trade." />
            </th>
            <th>
              Profit
              <InfoTooltip text="Gain ou perte actuel basé sur le prix live Binance." />
            </th>
            <th>
              Timestamp
              <InfoTooltip text="Heure et date d’ouverture du trade." />
            </th>
            <th>🛑</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(trades).map(([symbol, info]) => {
            const buyPrice = parseFloat(info.achat);
            const usdtInvested = parseFloat(info.usdt);
            const livePrice = livePrices[symbol] || 0;
            const amount = usdtInvested / buyPrice;
            const profit = ((livePrice - buyPrice) * amount).toFixed(2);
            const isProfit = parseFloat(profit) >= 0;

            return (
              <tr key={symbol} className="border-b border-zinc-800">
                <td>{symbol}</td>
                <td>{(buyPrice ?? 0).toFixed(4)}</td>
                <td>{usdtInvested}</td>
                <td className={isProfit ? "text-green-400" : "text-red-400"}>
                  {profit} $
                </td>
                <td>{new Date(info.timestamp * 1000).toLocaleString()}</td>
                <td>
                  <button
                    onClick={() => stopTrade(symbol, mode)}
                    className="text-red-400 hover:text-red-600 font-bold"
                  >
                    Stop
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  };

  return (
    <div className="p-4 bg-zinc-900 rounded-xl shadow-lg mt-6">
      <h2 className="text-lg font-bold text-white mb-4">
        ⚡ Trades Actifs
        <InfoTooltip text="Liste des positions actuellement ouvertes par l'IA en mode fictif ou réel." />
      </h2>

      <h3 className="text-yellow-400 font-semibold mb-2">
        Mode Fictif
        <InfoTooltip text="Le mode fictif simule les trades sans utiliser d'argent réel. Pratique pour les tests." />
      </h3>
      {renderTrades("fictif")}

      <h3 className="text-emerald-400 font-semibold mt-6 mb-2">
        Mode Réel
        <InfoTooltip text="Le mode réel exécute des ordres sur Binance avec de l'argent réel." />
      </h3>
      {renderTrades("reel")}
    </div>
  );
};

export default ActiveTradesPanel;
