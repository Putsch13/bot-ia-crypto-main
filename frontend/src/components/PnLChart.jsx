import React, { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API_URL = "http://127.0.0.1:5002";

export default function PnLChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchChart = async () => {
      try {
        const res = await axios.get(`${API_URL}/performance`);
        setData(res.data.data.gains_by_day || []);
      } catch (err) {
        console.error("Erreur chargement PnL chart :", err);
      }
    };
    fetchChart();
  }, []);

  if (!data.length) return <p className="text-zinc-400">Aucune donnée PnL</p>;

  return (
    <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
      <h2 className="text-xl font-semibold mb-4">📈 Évolution des gains quotidiens</h2>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#444" />
          <XAxis dataKey="date" stroke="#aaa" />
          <YAxis stroke="#aaa" />
          <Tooltip />
          <Line type="monotone" dataKey="gain" stroke="#22c55e" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
