export default function HomeScreen({ mode, onStart, onHistory }) {
  const isPersonal = mode === "personal";
  return (
    <div className={`min-h-screen flex flex-col items-center justify-center gap-6
                    bg-gradient-to-br
                    ${isPersonal
                      ? "from-navy via-[#1a2a4a] to-[#0d1b2e]"
                      : "from-gray-800 via-gray-700 to-gray-900"}
                    px-6 py-10`}>

      {/* Logo */}
      <div className="text-center">
        <h1 className="text-7xl font-black text-white tracking-tighter">
          AU<span className="text-electric">RA</span>
        </h1>
        <p className="text-white/60 text-sm mt-1 font-medium">
          Autonomous Understanding & Response Agent
        </p>
      </div>

      {/* Mode Banner */}
      <div
        className={`w-full max-w-sm rounded-2xl border px-6 py-6 text-center
                    transition-all duration-300
                    ${isPersonal
                      ? "bg-electric/10 border-electric/30"
                      : "bg-white/5 border-white/10"}
        `}
      >
        <div className="flex flex-col items-center gap-2">

          <div className="text-white font-bold text-base">
            {isPersonal ? "👤 Personal Mode Active" : "🧍 Helper Mode"}
          </div>

          <div className="text-white/50 text-sm leading-relaxed max-w-[260px]">
            {isPersonal
              ? "Your medical profile will personalize guidance"
              : "Safe defaults active — no profile required"}
          </div>

        </div>
      </div>

      {/* HELP Button */}
      <button
        onClick={onStart}
        className="relative overflow-hidden w-44 h-44 rounded-full bg-danger text-white font-black text-2xl
                  flex flex-col items-center justify-center gap-1
                  animate-pulse-ring shadow-2xl active:scale-95 transition-transform duration-150
                  focus:outline-none select-none"
      >

        {/* Ripple layer */}
        <span className="absolute inset-0 rounded-full bg-white/10 opacity-0 active:opacity-100 transition"></span>

        {/* Content */}
        <span className="text-5xl relative z-10">🆘</span>
        <span className="relative z-10">HELP</span>

      </button>

      {/* History link */}
      <button
        onClick={onHistory}
        className="text-white/30 text-xs underline hover:text-white/60 transition-colors"
      >
        View past sessions
      </button>
    </div>
  );
}
