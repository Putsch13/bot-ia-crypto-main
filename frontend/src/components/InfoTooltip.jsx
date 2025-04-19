import React from "react";

export default function InfoTooltip({ text }) {
  return (
    <span className="group relative inline-block ml-1 cursor-help">
      <span className="text-sm text-blue-400">ℹ️</span>
      <div className="absolute hidden group-hover:block bg-zinc-800 text-white text-xs rounded p-2 shadow-xl w-64 z-50 top-full mt-1 left-1/2 transform -translate-x-1/2">
        {text}
      </div>
    </span>
  );
}
