// frontend/src/components/HistoryPanel.jsx
import React, { useEffect, useState } from 'react';

const HistoryPanel = () => {
  const [trades, setTrades] = useState([]);
  const [filter, setFilter] = useState({ mode: 'all', symbol: '', search: '' });

  useEffect(() => {
    fetch('/historique')
      .then((res) => res.json())
      .then((data) => setTrades(data.reverse())) // du plus récent au plus ancien
      .catch((err) => console.error(err));
  }, []);

  const filteredTrades = trades.filter((trade) => {
    const modeOk = filter.mode === 'all' || trade.Mode === filter.mode;
    const symbolOk = !filter.symbol || trade.Symbol.includes(filter.symbol.toUpperCase());
    const commentOk = trade.Commentaire.toLowerCase().includes(filter.search.toLowerCase());
    return modeOk && symbolOk && commentOk;
  });

  const resume = {
    total: filteredTrades.length,
    totalGain: filteredTrades.reduce((acc, t) => acc + parseFloat(t['Gain (%)'].replace('%', '')), 0).toFixed(2),
    winrate: (
      (filteredTrades.filter((t) => parseFloat(t['Gain (%)']) > 0).length / filteredTrades.length) *
      100
    ).toFixed(1),
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Historique des Trades</h2>

      {/* Résumé */}
      <div className="mb-4 p-4 bg-gray-100 rounded-lg shadow">
        <p><strong>Total trades :</strong> {resume.total}</p>
        <p><strong>Gain cumulé :</strong> {resume.totalGain}%</p>
        <p><strong>Winrate :</strong> {isNaN(resume.winrate) ? '-' : `${resume.winrate}%`}</p>
      </div>

      {/* Filtres */}
      <div className="mb-4 flex gap-4 items-center">
        <select
          value={filter.mode}
          onChange={(e) => setFilter({ ...filter, mode: e.target.value })}
          className="border px-2 py-1 rounded"
        >
          <option value="all">Tous</option>
          <option value="reel">Réel</option>
          <option value="fictif">Fictif</option>
        </select>
        <input
          type="text"
          placeholder="Filtrer par crypto (ex: BTC)"
          value={filter.symbol}
          onChange={(e) => setFilter({ ...filter, symbol: e.target.value })}
          className="border px-2 py-1 rounded"
        />
        <input
          type="text"
          placeholder="Commentaire / recherche"
          value={filter.search}
          onChange={(e) => setFilter({ ...filter, search: e.target.value })}
          className="border px-2 py-1 rounded flex-1"
        />
      </div>

      {/* Tableau */}
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-200">
            <th className="border px-2 py-1">Date</th>
            <th className="border px-2 py-1">Mode</th>
            <th className="border px-2 py-1">Crypto</th>
            <th className="border px-2 py-1">Achat</th>
            <th className="border px-2 py-1">Vente</th>
            <th className="border px-2 py-1">Gain %</th>
            <th className="border px-2 py-1">Commentaire</th>
          </tr>
        </thead>
        <tbody>
          {filteredTrades.map((trade, i) => (
            <tr key={i} className="text-sm text-center hover:bg-gray-50">
              <td className="border px-2 py-1">{trade.Date}</td>
              <td className="border px-2 py-1">{trade.Mode}</td>
              <td className="border px-2 py-1">{trade.Symbol}</td>
              <td className="border px-2 py-1">{trade['Prix Achat']}</td>
              <td className="border px-2 py-1">{trade['Prix Vente']}</td>
              <td className="border px-2 py-1">{trade['Gain (%)']}</td>
              <td className="border px-2 py-1">{trade.Commentaire}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default HistoryPanel;
