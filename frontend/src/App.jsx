import React from "react";
import IASettings from "./components/IASettings";
import IAReportView from "./components/IAReportView";
import IAReportLive from "./components/IAReportLive";
import TopFlopCards from "./components/TopFlopCards";
import LogPanel from "./components/LogPanel";
import DashboardPerf from "./components/DashboardPerf";
import PnLChart from "./components/PnLChart";
import IAReportGPT from "./components/IAReportGPT";
import GPTNarrator from "./components/GPTNarrator";
import ActiveTradesPanel from './components/ActiveTradesPanel';

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white py-8 px-4 lg:px-12">
      {/* Header */}
      <header className="mb-10">
        <h1 className="text-4xl font-bold mb-2">🤖 Bot IA Crypto – Tableau de bord</h1>
        <p className="text-zinc-400 max-w-2xl">
          Pilotez votre stratégie d’investissement crypto avec intelligence. Visualisez les performances, ajustez les paramètres, et laissez l’IA faire le reste.
        </p>
      </header>

      {/* Dashboard perf */}
      <div className="mb-8">
        <DashboardPerf />
      </div>

      {/* PnL Chart */}
      <div className="mb-8">
        <PnLChart />
      </div>

      {/* Rapport IA GPT */}
      <div className="mb-8">
        <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4">🧠 Rapport IA (GPT Style)</h2>
          <IAReportGPT />
        </div>
      </div>

      {/* Narration IA */}
      <div className="mb-8">
        <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
          <h2 className="text-xl font-semibold mb-4">🎙️ Narration IA</h2>
          <GPTNarrator />
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bloc gauche */}
        <div className="space-y-6">
          <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">⚙️ Paramètres IA</h2>
            <IASettings />
          </div>
        </div>

        {/* Bloc droit */}
        <div className="space-y-6">
          <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">📡 Activité Live</h2>
            <IAReportLive />
          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">🧠 Analyse IA</h2>
            <IAReportView />
          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">🚀 Top / Flop du jour</h2>
            <TopFlopCards />
          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">🪵 Historique des logs</h2>
            <LogPanel />
          </div>

          <div className="bg-zinc-900 p-6 rounded-2xl shadow-lg">
            <h2 className="text-xl font-semibold mb-4">📈 Positions en cours</h2>
            <ActiveTradesPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
