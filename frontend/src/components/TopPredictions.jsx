import React, { useEffect, useState } from 'react';

const TopPredictions = () => {
  const [topCoins, setTopCoins] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5002/top-predictions")
      .then(res => res.json())
      .then(data => setTopCoins(data))
      .catch(err => console.error("Erreur API /top-predictions:", err));
  }, []);

  return (
    <div className="bg-zinc-900 text-white p-6 rounded-2xl shadow-xl w-full max-w-2xl mx-auto mt-10">
      <h2 className="text-xl font-bold mb-4">📈 Top cryptos IA</h2>
      <ul className="space-y-2">
        {topCoins.map((coin, index) => (
          <li key={coin.symbol} className="flex justify-between items-center bg-zinc-800 p-3 rounded-xl">
            <span className="text-lg font-medium">{index + 1}. {coin.symbol}</span>
            <span className="text-green-400 font-semibold">🚀 {coin.proba * 100}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TopPredictions;
