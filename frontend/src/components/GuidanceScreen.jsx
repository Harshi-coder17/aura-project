// frontend/src/components/GuidanceScreen.jsx
import { useEffect, useRef, useState } from "react";

const RISK_STYLES = {
  LOW:      { badge: "bg-green-100 text-green-800",         label: "✅ LOW RISK",  border: "border-green-400" },
  MEDIUM:   { badge: "bg-amber-100 text-amber-800",         label: "⚠️ MODERATE",  border: "border-amber-400" },
  HIGH:     { badge: "bg-red-100 text-red-800",             label: "🚨 HIGH RISK", border: "border-red-500"   },
  CRITICAL: { badge: "bg-red-600 text-white animate-pulse", label: "🆘 CRITICAL",  border: "border-red-600"   },
};

export default function GuidanceScreen({ result, onBack, onViewMap }) {
  const risk    = result?.risk_level   || "LOW";
  const isPanic = risk === "HIGH" || risk === "CRITICAL";
  const steps   = result?.response_steps || [];
  const action  = result?.action_plan    || {};
  const fam     = result?.fam_result     || {};
  const echo    = result?.echo_result    || {};
  const style   = RISK_STYLES[risk] || RISK_STYLES.LOW;

  const transport     = action.transport || "";
  const isAmbulance   = transport === "AMBULANCE";
  const isCab         = transport === "PRIORITY_CAB";
  const famSeverity   = fam.severity || "";

  // Show ambulance button when: transport is AMBULANCE
  const showAmbulance = isAmbulance;

  // Show cab button when:
  // - transport is PRIORITY_CAB, OR
  // - transport is AMBULANCE AND severity is HIGH (not CRITICAL) — give user the choice
  const showCab = isCab || (isAmbulance && famSeverity === "HIGH");

  const [holdProgress, setHoldProgress] = useState(0);
  const [voicePlayed, setVoicePlayed]   = useState(false);
  const holdIntervalRef = useRef(null);
  const holdTimerRef    = useRef(null);

  // Auto-play voice for HIGH / CRITICAL only
  useEffect(() => {
    if (isPanic && result?.voice_text && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utter  = new SpeechSynthesisUtterance(result.voice_text);
      utter.rate   = 0.82;
      utter.pitch  = 1.0;
      utter.volume = 1.0;
      utter.onend  = () => setVoicePlayed(true);
      window.speechSynthesis.speak(utter);
      setVoicePlayed(true);
    }
    return () => window.speechSynthesis?.cancel();
  }, [result, isPanic]);

  const handleVoice = () => {
    if (!result?.voice_text || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u  = new SpeechSynthesisUtterance(result.voice_text);
    u.rate   = 0.82;
    u.pitch  = 1.0;
    u.volume = 1.0;
    u.onend  = () => setVoicePlayed(true);
    window.speechSynthesis.speak(u);
    setVoicePlayed(true);
  };

  const startHold = () => {
    let progress = 0;
    holdIntervalRef.current = setInterval(() => {
      progress += 100 / 30;
      setHoldProgress(Math.min(progress, 100));
      if (progress >= 100) clearInterval(holdIntervalRef.current);
    }, 100);
    holdTimerRef.current = setTimeout(() => {
      window.open("tel:108");
    }, 3000);
  };

  const cancelHold = () => {
    clearTimeout(holdTimerRef.current);
    clearInterval(holdIntervalRef.current);
    setHoldProgress(0);
  };

  useEffect(() => () => cancelHold(), []);

  return (
    <div className={`min-h-screen bg-white flex flex-col px-6 pt-20 pb-8
                     gap-4 relative ${isPanic ? "bg-red-50/30" : ""}`}>

      <button onClick={onBack}
        className="absolute top-5 left-5 text-2xl text-navy
                   hover:text-electric transition-colors">
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
          {fam.injury || "Assessing condition…"}
        </div>
        <div className="text-gray-500 text-xs mt-1">
          Severity: {fam.severity || "—"}
          {fam.body_part         ? ` • ${fam.body_part}`               : ""}
          {echo.calibration_mode ? ` • Mode: ${echo.calibration_mode}` : ""}
        </div>
        {fam.personal_flags?.length > 0 && (
          <div className="mt-2 text-xs text-amber-700 bg-amber-50
                          rounded-lg px-3 py-1.5">
            ⚠️ Personal flags: {fam.personal_flags.join(", ")}
          </div>
        )}
      </div>

      {/* Transport label */}
      {transport && (
        <div className="text-sm text-gray-500">
          Recommended Transport:{" "}
          <span className="text-navy font-semibold">
            {isAmbulance ? "🚑 Ambulance"    :
             isCab       ? "🚕 Priority Cab" :
             "🚶 Self / None"}
          </span>
        </div>
      )}

      {/* Steps */}
      <div className="flex flex-col gap-3">
        {steps.map((step, i) => (
          <div key={i}
            className={`flex gap-3 items-start p-4 rounded-2xl border-l-4
                        bg-gray-50 animate-fade-in ${style.border}`}>
            <div className="min-w-8 h-8 rounded-full bg-electric text-white
                            flex items-center justify-center font-bold
                            text-sm shrink-0">
              {i + 1}
            </div>
            <p className={`leading-relaxed font-medium
                           ${isPanic ? "text-lg font-bold" : "text-sm"}`}>
              {step}
            </p>
          </div>
        ))}
      </div>

      {/* ── Action Buttons ─────────────────────────────────────────── */}
      <div className="flex gap-3">

        {/* AMBULANCE — hold to call */}
        {showAmbulance && (
          <div className="flex-1 bg-red-50 border border-red-200 rounded-2xl
                          p-4 flex flex-col gap-3 relative overflow-hidden">
            <div
              className="absolute left-0 top-0 h-full bg-red-200/40
                         transition-all duration-100 pointer-events-none"
              style={{ width: `${holdProgress}%` }}
            />
            <div className="relative z-10 flex flex-col items-center gap-2">
              <span className="text-5xl">🚑</span>
              <span className="text-base font-bold text-red-700">
                Call Ambulance
              </span>
              {famSeverity === "HIGH" && (
                <span className="text-xs text-red-400 text-center">
                  If condition worsens
                </span>
              )}
              <button
                className="relative mt-2 w-full border-2 border-red-500
                           bg-red-50 text-red-600 py-4 rounded-xl font-semibold
                           flex flex-col items-center gap-1 overflow-hidden
                           active:scale-95 transition-transform select-none
                           focus:outline-none"
                onMouseDown={startHold}
                onMouseUp={cancelHold}
                onMouseLeave={cancelHold}
                onTouchStart={(e) => { e.preventDefault(); startHold(); }}
                onTouchEnd={cancelHold}
                onTouchCancel={cancelHold}
              >
                <span className="text-2xl">🚑</span>
                <span className="text-base font-bold">
                  {holdProgress > 0 ? "Calling…" : "Call Ambulance"}
                </span>
                <span className="text-xs text-red-500/80">
                  Press &amp; hold 3 seconds
                </span>
                <div
                  className="absolute bottom-0 left-0 h-1.5 bg-red-500
                             transition-all duration-100"
                  style={{ width: `${holdProgress}%` }}
                />
              </button>
            </div>
          </div>
        )}

        {/* PRIORITY CAB */}
        {showCab && (
          <button
            onClick={() =>
              window.open("https://www.google.com/maps/search/cabs+near+me")
            }
            className="flex-1 border-2 border-amber-400 bg-amber-50
                       text-amber-700 rounded-2xl p-5 font-bold flex flex-col
                       items-center gap-2 active:scale-95 transition-transform"
          >
            <span className="text-3xl">🚕</span>
            <span className="text-base font-bold">Book Priority Cab</span>
            <span className="text-xs text-amber-700/80 text-center">
              {isAmbulance
                ? "Or take cab if closer"
                : "Fast transport to hospital"}
            </span>
            <span className="text-xs font-semibold text-amber-800">
              Find Nearby →
            </span>
          </button>
        )}

        {/* FIND HOSPITALS — always visible */}
        <button
          onClick={onViewMap}
          className="flex-1 bg-blue-50 text-navy rounded-2xl p-5 flex
                     flex-col items-center justify-center gap-2
                     active:scale-95 transition-all border border-blue-100
                     hover:bg-blue-100"
        >
          <span className="text-3xl">🏥</span>
          <span className="text-base font-bold">Find Hospitals</span>
          <span className="text-xs text-gray-500">View nearby &amp; ETA</span>
          <span className="text-xs text-blue-600 font-semibold">Open Map →</span>
        </button>
      </div>

      {/* Voice Button — works for all risk levels */}
      {result?.voice_text && (
        <button
          onClick={handleVoice}
          className="w-full border-2 border-electric text-electric rounded-2xl
                     py-3 font-bold text-sm hover:bg-electric/5 transition-colors"
        >
          {isPanic
            ? "🔊 Replay Voice Instructions"
            : "🔊 Hear Voice Instructions"}
        </button>
      )}
    </div>
  );
}