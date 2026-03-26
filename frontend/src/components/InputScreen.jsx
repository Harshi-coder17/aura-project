import { useState, useRef } from "react";

export default function InputScreen({ mode, onBack, onSubmit, loading }) {
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const recRef = useRef(null);
  const isPersonal = mode === "personal";

  const startRecording = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert("Voice not supported. Please type your emergency."); return; }
    recRef.current = new SR();
    recRef.current.lang = "en-IN";
    recRef.current.continuous = false;
    recRef.current.interimResults = false;
    recRef.current.onresult = (e) => setText(e.results[0][0].transcript);
    recRef.current.onend = () => setRecording(false);
    recRef.current.onerror = () => setRecording(false);
    recRef.current.start();
    setRecording(true);
  };

  const stopRecording = () => {
    recRef.current?.stop();
    setRecording(false);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col px-6 pt-20 pb-8 gap-5 relative">
      <button onClick={onBack}
        className="absolute top-5 left-5 text-2xl text-navy hover:text-electric transition-colors">
        ←
      </button>

      <div className="text-center">
        <h2 className="text-2xl font-extrabold text-navy">
          {isPersonal ? "👤 What happened?" : "🧍 Describe the emergency"}
        </h2>
        <p className="text-gray-400 text-sm mt-1">
          {isPersonal
            ? "AURA will use your profile for personalized guidance"
            : "Stranger mode — safe defaults will apply"}
        </p>
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={isPersonal
          ? "Describe what happened to you... (e.g. burn on my right hand)"
          : "Describe the emergency for the person you are helping..."}
        rows={5}
        className="w-full rounded-2xl border-2 border-gray-200 focus:border-electric
                   outline-none p-4 text-base resize-none font-medium transition-colors"
      />

      {/* Mic button */}
      <button
        onClick={recording ? stopRecording : startRecording}
        className={`self-center w-20 h-20 rounded-full text-white text-3xl font-bold
                    transition-all duration-200 shadow-lg focus:outline-none
                    ${recording
                      ? "bg-danger animate-pulse scale-110"
                      : "bg-electric hover:bg-blue-600 active:scale-95"}`}
      >
        {recording ? "⏹" : "🎤"}
      </button>

      {recording && (
        <p className="text-center text-danger text-sm font-semibold animate-pulse">
          Listening... tap to stop
        </p>
      )}

      <button
        onClick={() => onSubmit(text)}
        disabled={!text.trim() || loading}
        className="w-full py-5 rounded-2xl bg-electric text-white text-lg font-bold
                   shadow-[0_4px_20px_rgba(30,144,255,0.4)] active:scale-97
                   disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        {loading ? "Analyzing emergency..." : "Get Emergency Help →"}
      </button>
    </div>
  );
}
