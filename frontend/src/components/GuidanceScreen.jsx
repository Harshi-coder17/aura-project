import { useEffect } from "react";

const RISK_STYLES = {
  LOW:      { badge: "bg-green-100 text-green-800", label: "✅ LOW RISK",      border: "border-safe" },
  MEDIUM:   { badge: "bg-amber-100 text-amber-800", label: "⚠️ MODERATE",      border: "border-amber" },
  HIGH:     { badge: "bg-red-100 text-red-800",    label: "🚨 HIGH RISK",      border: "border-danger" },
  CRITICAL: { badge: "bg-danger text-white animate-pulse", label: "🆘 CRITICAL", border: "border-danger" },
};

export default function GuidanceScreen({ result, onBack, onViewMap }) {
  const risk = result?.risk_level;
  const isPanic = risk === "HIGH" || risk === "CRITICAL";
  const steps = result?.response_steps || [];
  const action = result?.action_plan || {};
  const fam = result?.fam_result || {};
  const echo = result?.echo_result || {};
  const style = RISK_STYLES[risk] || RISK_STYLES.LOW;

  useEffect(() => {
    if (isPanic && result?.voice_text && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(result.voice_text);
      utter.rate = 0.82;
      utter.pitch = 1.0;
      utter.volume = 1.0;
      window.speechSynthesis.speak(utter);
    }
    return () => window.speechSynthesis?.cancel();
  }, [result, isPanic]);

  const replayVoice = () => {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(result?.voice_text);
    u.rate = 0.82;
    window.speechSynthesis.speak(u);
  };

  return (
    <div className={`min-h-screen bg-white flex flex-col px-6 pt-20 pb-8 gap-4 relative
                    ${isPanic ? "bg-red-50/30" : ""}`}>
      
      <button
        onClick={onBack}
        className="absolute top-5 left-5 text-2xl text-navy hover:text-electric transition-colors"
      >
        ←
      </button>

      {/* Risk Badge */}
      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full
                       text-sm font-bold self-start ${style.badge}`}>
        {style.label}
        <span className="text-xs opacity-70">
          {((result?.risk_score || 0) * 100).toFixed(0)}% risk
        </span>
      </div>

      {/* Injury Summary */}
      <div className="bg-blue-50 rounded-2xl p-4 border border-blue-100">
        <div className="font-extrabold text-navy text-base uppercase tracking-wide">
          {fam.injury}
        </div>
        <div className="text-gray-500 text-xs mt-1">
          Severity: {fam.severity}
          {fam.body_part ? ` • ${fam.body_part}` : ""}
          {echo.calibration_mode ? ` • Mode: ${echo.calibration_mode}` : ""}
        </div>
        {fam.personal_flags?.length > 0 && (
          <div className="mt-2 text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-1.5">
            ⚠️ Personal flags: {fam.personal_flags.join(", ")}
          </div>
        )}
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-3">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex gap-3 items-start p-4 rounded-2xl border-l-4
                        bg-gray-50 animate-fade-in ${style.border}`}
          >
            <div
              className={`min-w-8 h-8 rounded-full bg-electric text-white
                          flex items-center justify-center font-bold text-sm shrink-0`}
            >
              {i + 1}
            </div>

            <p
              className={`leading-relaxed font-medium
                          ${isPanic ? "text-lg font-bold" : "text-sm"}`}
            >
              {step}
            </p>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {(action.transport === "AMBULANCE" || action.transport === "PRIORITY_CAB") && (
          <button
            onClick={() => window.open("tel:108")}
            className="flex-1 bg-danger text-white rounded-2xl p-3 font-bold text-sm
                       flex flex-col items-center gap-1 active:scale-95 transition-transform"
          >
            <span className="text-2xl">🚑</span>
            <span>Call 108</span>
            <span className="text-xs opacity-80">Ambulance</span>
          </button>
        )}

        {action.transport === "PRIORITY_CAB" && (
          <button
            onClick={() => alert("Priority cab feature coming soon")}
            className="flex-1 bg-amber text-white rounded-2xl p-3 font-bold text-sm
                       flex flex-col items-center gap-1 active:scale-95 transition-transform"
          >
            <span className="text-2xl">🚕</span>
            <span>Book Cab</span>
            <span className="text-xs opacity-80">Priority</span>
          </button>
        )}

        <button
          onClick={onViewMap}
          className="flex-1 bg-blue-50 text-navy rounded-2xl p-3 font-bold text-sm
                     flex flex-col items-center gap-1 active:scale-95 transition-transform"
        >
          <span className="text-2xl">🏥</span>
          <span>Hospitals</span>
          <span className="text-xs opacity-60">Map →</span>
        </button>
      </div>

      {/* Voice Replay */}
      <button
        onClick={replayVoice}
        className="w-full border-2 border-electric text-electric rounded-2xl py-3
                   font-bold text-sm hover:bg-electric/5 transition-colors"
      >
        🔊 Replay Voice Instructions
      </button>
    </div>
  );
}