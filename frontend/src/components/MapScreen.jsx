import { useState, useEffect } from "react";
import BACKEND_URL from "../config";

export default function MapScreen({ result, onBack }) {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHospitals = async () => {
      try {
        const loc = result?.action_plan?.hospital;
        const url = `${BACKEND_URL}/api/v1/hospitals?lat=0&lon=0`;
        const res = await fetch(url);
        const data = await res.json();
        setHospitals(data.hospitals || []);
      } catch {
        // Fallback mock data
        setHospitals([
          { name: "City General Hospital", distance_km: 1.5, eta_minutes: 8,
            address: "123 Main Street", phone: "108" },
          { name: "Apollo Hospital", distance_km: 2.8, eta_minutes: 12,
            address: "456 Park Road", phone: "1066" },
          { name: "Community Medical Center", distance_km: 4.1, eta_minutes: 18,
            address: "789 Lake View", phone: "102" },
        ]);
      } finally {
        setLoading(false);
      }
    };
    fetchHospitals();
  }, []);

  return (
    <div className="min-h-screen bg-white flex flex-col px-6 pt-20 pb-8 gap-4 relative">
      <button onClick={onBack}
        className="absolute top-5 left-5 text-2xl text-navy hover:text-electric transition-colors">
        ←
      </button>
      <h2 className="text-xl font-extrabold text-navy">🏥 Nearest Hospitals</h2>
      <p className="text-gray-400 text-xs -mt-2">Tap any hospital to call directly</p>

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
                         hover:shadow-md transition-shadow text-left w-full border border-gray-100"
            >
              <span className="text-3xl">🏥</span>
              <div className="flex-1">
                <div className="font-bold text-navy text-sm">{h.name}</div>
                <div className="text-gray-400 text-xs mt-0.5">
                  {h.address} • 📞 {h.phone || "108"}
                </div>
                <div className="text-gray-400 text-xs">{h.distance_km} km away</div>
              </div>
              <div className="text-right shrink-0">
                <div className="text-2xl font-black text-electric">{h.eta_minutes}</div>
                <div className="text-gray-400 text-xs">min ETA</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
