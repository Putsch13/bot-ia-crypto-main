import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Papa from 'papaparse';

const LogChart = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch('/logs/ia_predictions_log.csv')
      .then(res => res.text())
      .then(csv => {
        const parsed = Papa.parse(csv, { header: true }).data;

        // Regrouper par symbol et compter SUCCESS / FAIL
        const grouped = {};
        parsed.forEach(entry => {
          const symbol = entry.symbol;
          const result = entry.result;
          if (!symbol || !result) return;

          if (!grouped[symbol]) {
            grouped[symbol] = { symbol, SUCCESS: 0, FAIL: 0 };
          }
          grouped[symbol][result]++;
        });

        setData(Object.values(grouped));
      });
  }, []);

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-xl shadow">
      <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-white">
        📊 Résultats des Prédictions IA (par crypto)
      </h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis dataKey="symbol" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="SUCCESS" fill="#22c55e" />
          <Bar dataKey="FAIL" fill="#ef4444" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LogChart;
