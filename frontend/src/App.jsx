<<<<<<< HEAD
import { useState } from "react";
import InputBox from "./components/InputBox";
import ResponseBox from "./components/ResponseBox";
import { sendMessage } from "./services/api";

function App() {
  const [response, setResponse] = useState(null);

  const handleSubmit = async (text) => {
    try {
      const data = await sendMessage(text);
      console.log("API Response:", data);
      setResponse(data);
    } catch (error) {
      console.error("Error:", error);
=======
import { useState, useEffect } from "react";
import ModeToggle   from "./components/ModeToggle";
import HomeScreen   from "./components/HomeScreen";
import InputScreen  from "./components/InputScreen";
import GuidanceScreen from "./components/GuidanceScreen";
import MapScreen    from "./components/MapScreen";
import Toast        from "./components/Toast";
import useAura      from "./hooks/useAura";

export default function App() {
  const [screen, setScreen] = useState("home");
  const [mode, setMode]     = useState(() =>
    localStorage.getItem("aura_mode") || "stranger");
  const [result, setResult] = useState(null);
  const [toast, setToast]   = useState(null);

  const { process, startSession, loading, error } = useAura();

  useEffect(() => { startSession(); }, []);

  const showToast = (msg, ms = 3000) => {
    setToast(msg);
    setTimeout(() => setToast(null), ms);
  };

  const handleModeToggle = (newMode) => {
    setMode(newMode);
    localStorage.setItem("aura_mode", newMode);
    showToast(newMode === "personal"
      ? "👤 Personal Mode — your profile is active"
      : "🧍 Stranger Mode — safe defaults active");
  };

  const handleSubmit = async (text) => {
    if (!text.trim()) return;
    try {
      const data = await process(text, mode);
      setResult(data);
      setScreen("guidance");
    } catch (err) {
      showToast(`❌ ${err.message}. Check backend connection.`);
>>>>>>> 73ffa1e (frontend updated)
    }
  };

  return (
<<<<<<< HEAD
    <div>
      <InputBox onSubmit={handleSubmit} />
      <ResponseBox data={response} />
    </div>
  );
}

export default App;
=======
    <div className="relative">
      <ModeToggle mode={mode} onToggle={handleModeToggle} />

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-navy/90 backdrop-blur-sm z-[9998]
                        flex flex-col items-center justify-center gap-5">
          <div className="w-16 h-16 rounded-full border-4 border-electric/20
                          border-t-electric animate-spin" />
          <p className="text-white font-semibold text-lg">AURA is analyzing...</p>
          <p className="text-white/40 text-sm">Processing all 8 agents</p>
        </div>
      )}

      {screen === "home"     && <HomeScreen mode={mode} onStart={() => setScreen("input")} onHistory={() => {}} />}
      {screen === "input"    && <InputScreen mode={mode} onBack={() => setScreen("home")} onSubmit={handleSubmit} loading={loading} />}
      {screen === "guidance" && result && <GuidanceScreen result={result} onBack={() => setScreen("input")} onViewMap={() => setScreen("map")} />}
      {screen === "map"      && <MapScreen result={result} onBack={() => setScreen("guidance")} />}

      <Toast message={toast} />
    </div>
  );
}
>>>>>>> 73ffa1e (frontend updated)
