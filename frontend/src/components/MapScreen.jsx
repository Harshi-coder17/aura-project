// frontend/src/components/MapScreen.jsx
import { useState, useEffect } from "react";
import BACKEND_URL from "../config";

const FALLBACK_HOSPITALS = [
  { name: "City General Hospital",    distance_km: 1.5, eta_minutes: 8,
    address: "123 Main Street",       phone: "108",
    capability: ["emergency", "trauma"] },
  { name: "Apollo Hospital",          distance_km: 2.8, eta_minutes: 12,
    address: "456 Park Road",         phone: "1066",
    capability: ["emergency", "cardiac", "burns"] },
  { name: "Community Medical Center", distance_km: 4.1, eta_minutes: 18,
    address: "789 Lake View",         phone: "102",
    capability: ["emergency"] },
];

export default function MapScreen({ result, onBack }) {
  const [hospitals, setHospitals]   = useState([]);
  const [loading, setLoading]       = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);

  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        // Pass location if available from result
        const loc = result?.action_plan?.hospital;
        const lat = loc?.lat ?? 0;
        const lon = loc?.lon ?? 0;

        const res  = await fetch(
          `${BACKEND_URL}/api/v1/hospitals?lat=${lat}&lon=${lon}`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const list = data.hospitals || [];

        if (list.length === 0) throw new Error("Empty hospital list");

        setHospitals(list);
        setUsingFallback(false);
      } catch (err) {
        console.warn("[MapScreen] Hospital fetch failed, using fallback:", err.message);
        setHospitals(FALLBACK_HOSPITALS);
        setUsingFallback(true);
      } finally {
        setLoading(false);
      }
    };
    fetchHospitals();
  }, []);

  return (
    <div className="min-h-screen bg-white flex flex-col px-6 pt-20 pb-8
                    gap-4 relative">

      <button
        onClick={onBack}
        className="absolute top-5 left-5 text-2xl text-navy
                   hover:text-electric transition-colors"
      >
        ←
      </button>

      <h2 className="text-xl font-extrabold text-navy">🏥 Nearest Hospitals</h2>
      <p className="text-gray-400 text-xs -mt-2">
        Tap any hospital to call directly
      </p>

      {/* Fallback notice */}
      {usingFallback && !loading && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl
                        px-4 py-2 text-xs text-amber-700">
          ⚠️ Showing default hospitals — location services unavailable
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-10 h-10 rounded-full border-4 border-electric/20
                          border-t-electric animate-spin" />
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {hospitals.map((h, i) => (
            <button
              key={i}
              onClick={() => window.open(`tel:${h.phone || "108"}`)}
              className="flex items-center gap-4 bg-gray-50 rounded-2xl p-4
                         hover:shadow-md transition-shadow text-left w-full
                         border border-gray-100 active:scale-[0.98]"
            >
              <span className="text-3xl">🏥</span>
              <div className="flex-1 min-w-0">
                <div className="font-bold text-navy text-sm truncate">
                  {h.name}
                </div>
                <div className="text-gray-400 text-xs mt-0.5 truncate">
                  {h.address} • 📞 {h.phone || "108"}
                </div>
                {h.capability?.length > 0 && (
                  <div className="text-gray-300 text-xs mt-0.5">
                    {h.capability.join(" · ")}
                  </div>
                )}
              </div>
              <div className="text-right shrink-0">
                <div className="text-2xl font-black text-electric">
                  {h.eta_minutes}
                </div>
                <div className="text-gray-400 text-xs">min ETA</div>
                <div className="text-gray-300 text-xs">{h.distance_km} km</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Always-visible emergency call button */}
      <button
        onClick={() => window.open("tel:108")}
        className="w-full bg-danger text-white rounded-2xl py-5 font-bold
                   text-lg shadow-lg active:scale-97 transition-transform mt-auto"
      >
        🚑 Call Ambulance (108)
      </button>
    </div>
  );
}