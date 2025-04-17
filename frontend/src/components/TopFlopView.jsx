import React, { useEffect, useState } from 'react';
import { getSentimentReport } from '../api.js';

const Card = ({ title, items }) => (
  <div className="bg-white rounded-xl p-4 shadow w-full">
    <h3 className="text-lg font-bold mb-2">{title}</h3>
    <ul className="space-y-1">
      {items.map((crypto, idx) => (
        <li key={idx} className="text-gray-800">{crypto}</li>
      ))}
    </ul>
  </div>
);

export default function TopFlopView() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getSentimentReport().then(setData);
  }, []);

  if (!data) return <p className="text-center">Chargement en cours...</p>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
      <Card title="🔥 Top 5 Cryptos" items={data.top} />
      <Card title="💩 Flop 5 Cryptos" items={data.flop} />
    </div>
  );
}
