import { useState, useEffect } from "react";

export default function ModeToggle({ mode, onToggle }) {
  const [animating, setAnimating] = useState(false);

  const handleToggle = (newMode) => {
    if (newMode === mode) return;
    setAnimating(true);
    setTimeout(() => setAnimating(false), 300);
    onToggle(newMode);
  };

  return (
    <div className="fixed top-4 right-4 z-50 bg-white/95 backdrop-blur-md
                    rounded-3xl p-1 shadow-xl flex items-center gap-1 border border-gray-100">

      {/* Personal Mode Pill */}
      <button
        onClick={() => handleToggle("personal")}
        title="Personal Mode — uses your medical profile"
        className={`
          flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl text-xs font-bold
          transition-all duration-300 ease-[cubic-bezier(.34,1.56,.64,1)]
          focus:outline-none select-none tracking-wide
          ${mode === "personal"
            ? "bg-electric text-white shadow-[0_4px_14px_rgba(30,144,255,0.5)] scale-105"
            : "bg-transparent text-gray-400 hover:text-gray-600"}
        `}
      >
        {mode === "personal" && (
          <span className="w-2 h-2 rounded-full bg-white animate-pulse inline-block" />
        )}
        <span>👤</span>
        <span>Personal</span>
      </button>

      {/* Divider */}
      <span className="w-px h-5 bg-gray-200" />

      {/* Stranger Mode Pill */}
      <button
        onClick={() => handleToggle("stranger")}
        title="Stranger/Helper Mode — no profile, safe defaults"
        className={`
          flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl text-xs font-bold
          transition-all duration-300 ease-[cubic-bezier(.34,1.56,.64,1)]
          focus:outline-none select-none tracking-wide
          ${mode === "stranger"
            ? "bg-[#636e72] text-white shadow-[0_4px_14px_rgba(99,110,114,0.4)] scale-105"
            : "bg-transparent text-gray-400 hover:text-gray-600"}
        `}
      >
        {mode === "stranger" && (
          <span className="w-2 h-2 rounded-full bg-white animate-pulse inline-block" />
        )}
        <span>🧍</span>
        <span>Stranger</span>
      </button>
    </div>
  );
}
