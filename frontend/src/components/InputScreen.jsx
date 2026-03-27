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
      
      {/* BACK BUTTON */}
      <button onClick={onBack}
        className="absolute top-5 left-5 text-2xl text-navy hover:text-electric transition-colors">
        ←
      </button>

      {/* HEADER */}
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

      {/* TEXT INPUT */}
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={isPersonal
          ? "Describe what happened to you... (e.g. burn on my right hand)"
          : "Describe the emergency for the person you are helping..."}
        rows={5}
        className="w-full rounded-2xl border-2 border-gray-200 focus:border-electric
                    focus:ring-2 focus:ring-electric/40
                   outline-none p-4 text-base resize-none font-medium transition-all"
      />

      {/* CAMERA + MIC SIDE BY SIDE */}
      <div className="flex items-center justify-center gap-6 mt-4 flex-wrap">

        {/* CAMERA BUTTON  */}
        <label
          htmlFor="imageUpload"
          className="w-20 h-20 rounded-full flex items-center justify-center
                     bg-gray-200 text-gray-700 text-3xl shadow-md border border-gray-300
                     hover:bg-gray-300 active:scale-95 transition-all cursor-pointer"
        >
          📷
        </label>

        {/* IMAGE INPUT  */}
        <input 
          type="file" 
          accept="image/*"
          className="hidden"
          id="imageUpload"
          onChange={(e) => {
            const file = e.target.files[0];
            if (file) {
              console.log("Image selected:", file);
            }
          }}
        />

        {/* MIC BUTTON */}
        <button
          onClick={recording ? stopRecording : startRecording}
          className={`w-20 h-20 rounded-full text-white text-4xl font-bold
                      transition-all duration-200 shadow-[0_6px_20px_rgba(59,130,246,0.35)] focus:outline-none
                      ${recording
                        ? "bg-danger animate-pulse scale-110"
                        : "bg-blue-500 hover:bg-blue-600 active:scale-95"}`}
        >
          {recording ? "⏹" : "🎤"}
        </button>

      </div>

      {/* MICRO UX ADDITION */}
      <p className="text-center text-gray-400 text-xs mt-1">
        You can type, speak, or upload an image
      </p>

      {/* RECORDING STATUS */}
      {recording && (
        <p className="text-center text-danger text-sm font-semibold animate-pulse">
          Listening... tap to stop
        </p>
      )}

      {/* SUBMIT BUTTON */}
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
