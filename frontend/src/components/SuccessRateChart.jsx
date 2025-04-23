import React, { useEffect, useState } from "react";
import Papa from "papaparse";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const SuccessRateChart = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("/logs/ia_predictions_log.csv")
      .then((res) => res.text())
      .then((csv) => {
        const parsed = Papa.parse(csv, { header: true }).data;

        // Regrouper par date
        const grouped = {};

        parsed.forEach((entry) => {
          const date = entry.datetime?.split(" ")[0];
          const result = entry.result;

          if (!date || !result) return;

          if (!grouped[date]) {
            grouped[date] = { date, total: 0, success: 0 };
          }

          grouped[date].total += 1;
          if (result === "SUCCESS") grouped[date].success += 1;
        });

        // Calcul du taux
        const formatted = Object.values(grouped).map((day) => ({
          date: day.date,
          successRate: Math.round((day.success / day.total) * 100),
        }));

        setData(formatted);
      });
  }, []);

  return (
    <div className="mt-6 p-4 bg-zinc-900 rounded-2xl shadow-lg">
      <h2 className="text-xl font-semibold mb-4 text-white">📈 Taux de Réussite IA par Jour (%)</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis dataKey="date" stroke="#fff" />
          <YAxis domain={[0, 100]} stroke="#fff" />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="successRate" stroke="#22c55e" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SuccessRateChart;
