import { useEffect } from "react";
import { useState } from "react";

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
  console.log("RISK:", risk);
  console.log("ACTION:", action.transport);
  const [holdProgress, setHoldProgress] = useState(0);
  let holdInterval;
  let holdTimer;
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

      {/* Transport Recommendation */}
      {action.transport && (
        <div className="text-sm text-gray-500 mb-2">
          Recommended Transport:{" "}
          <span className="text-navy font-semibold">
            {action.transport?.toUpperCase() === "AMBULANCE"
              ? "Ambulance"
              : action.transport?.toUpperCase() === "PRIORITY_CAB"
              ? "Priority Cab"
              : "Self / None"}
          </span>
        </div>
      )}

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
        {action.transport?.toUpperCase() === "AMBULANCE" && (
          <div className="flex-1 bg-red-50 border border-red-200 rounded-2xl p-4
                          flex flex-col gap-3 relative overflow-hidden">

            {/* PROGRESS BAR */}
            <div
              className="absolute left-0 top-0 h-full bg-red-200/40 transition-all duration-100"
              style={{ width: `${holdProgress}%` }}
            />

            {/* CONTENT */}
            <div className="relative z-10 flex flex-col items-center gap-2">

              <span className="text-5xl">🚑</span>

              <span className="text-base font-bold text-red-700">
                Call Ambulance
              </span>

              <span className="text-xs text-red-500 text-center">
                Press & hold for 3 seconds to call ambulance
              </span>

              {/* HOLD AREA */}
              <button
                className="relative mt-3 w-full border-2 border-danger bg-red-50 text-danger
                          py-4 rounded-xl font-semibold flex flex-col items-center gap-1
                          overflow-hidden active:scale-95 transition-transform"

                onMouseDown={() => {
                  let progress = 0;

                  holdInterval = setInterval(() => {
                    progress += 100 / 30;
                    setHoldProgress(progress);

                    if (progress >= 100) {
                      clearInterval(holdInterval);
                    }
                  }, 100);

                  holdTimer = setTimeout(() => {
                    window.open("tel:108");
                  }, 3000);
                }}

                onMouseUp={() => {
                  clearTimeout(holdTimer);
                  clearInterval(holdInterval);
                  setHoldProgress(0);
                }}

                onMouseLeave={() => {
                  clearTimeout(holdTimer);
                  clearInterval(holdInterval);
                  setHoldProgress(0);
                }}

                onTouchStart={() => {
                  let progress = 0;

                  holdInterval = setInterval(() => {
                    progress += 100 / 30;
                    setHoldProgress(progress);

                    if (progress >= 100) {
                      clearInterval(holdInterval);
                    }
                  }, 100);

                  holdTimer = setTimeout(() => {
                    window.open("tel:108");
                  }, 3000);
                }}

                onTouchEnd={() => {
                  clearTimeout(holdTimer);
                  clearInterval(holdInterval);
                  setHoldProgress(0);
                }}
              >
                {/* 🚑 Icon */}
                <span className="text-2xl">🚑</span>

                {/* Main Text */}
                <span className="text-base font-bold">
                  {holdProgress > 0 ? "Calling Ambulance..." : "Call Ambulance"}
                </span>

                {/* Instruction */}
                <span className="text-xs text-danger/80">
                  Press & hold for 3 seconds
                </span>

                {/* 🔥 Progress Bar */}
                <div
                  className="absolute bottom-0 left-0 h-1.5 bg-danger transition-all duration-100"
                  style={{ width: `${holdProgress}%` }}
                />
              </button>

            </div>
          </div>
        )}

        {action.transport === "PRIORITY_CAB" && (
          <button
            onClick={() => {
              const query = encodeURIComponent("nearest cab service");
              window.open("https://www.google.com/maps/search/cabs+near+me");
            }}
            className="flex-1 border-2 border-amber-400 bg-amber-50 text-amber-700
                      rounded-2xl p-5 font-bold flex flex-col items-center gap-2
                      active:scale-95 transition-transform relative overflow-hidden"
          >
            {/* 🚕 Icon */}
            <span className="text-3xl">🚕</span>

            {/* Title */}
            <span className="text-base font-bold">
              Book Priority Cab
            </span>

            {/* Description */}
            <span className="text-xs text-amber-700/80 text-center">
              Fast transport for non-critical cases
            </span>

            {/* CTA */}
            <span className="text-xs font-semibold text-amber-800">
              Find Nearby →
            </span>
          </button>
        )}

        <button
          onClick={onViewMap}
          className="flex-1 bg-blue-50 text-navy rounded-2xl p-5
                    flex flex-col items-center justify-center gap-2
                    active:scale-95 transition-all duration-200
                    border border-blue-100 hover:bg-blue-100"
        >
          {/* Icon */}
          <span className="text-3xl">🏥</span>

          {/* Title */}
          <span className="text-base font-bold">
            Find Hospitals
          </span>

          {/* Subtext */}
          <span className="text-xs text-gray-500">
            View nearby hospitals & ETA
          </span>

          {/* CTA */}
          <span className="text-xs text-blue-600 font-semibold">
            Open Map →
          </span>
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