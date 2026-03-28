// frontend/src/hooks/useAura.js
import { useState, useRef, useCallback, useEffect } from "react";
import BACKEND_URL from "../config";

export default function useAura() {
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  const sessionId  = useRef(crypto.randomUUID());
  const turnRef    = useRef(1);
  const locationRef = useRef(null); // cached geolocation

  // ── Get geolocation once on mount (best-effort, never blocks) ──────
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        locationRef.current = {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        };
        console.log("[AURA] Location cached:", locationRef.current);
      },
      (err) => {
        console.warn("[AURA] Geolocation denied or unavailable:", err.message);
        locationRef.current = null;
      },
      { timeout: 5000, maximumAge: 60000 }
    );
  }, []);

  // ── Session init (safe fallback) ───────────────────────────────────
  const startSession = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/session/start`, {
        method: "POST",
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      if (data?.session_id) sessionId.current = data.session_id;
    } catch {
      sessionId.current = crypto.randomUUID();
      console.warn("[AURA] Using fallback session ID");
    }
  }, []);

  // ── Main process function ──────────────────────────────────────────
  const process = useCallback(async (text, mode, userId = null) => {
    setLoading(true);
    setError(null);

    try {
      const payload = {
        session_id:   sessionId.current,
        user_id:      mode === "personal" ? (userId || "user_demo") : null,
        mode:         mode,
        text:         text,
        turn_number:  turnRef.current++,
        location:     locationRef.current,   // null if denied → backend uses mock
      };

      console.log("[AURA] Sending to backend:", payload);

      const res = await fetch(`${BACKEND_URL}/api/v1/process`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      console.log("[AURA] Backend response:", data);

      if (!data || typeof data !== "object") {
        throw new Error("Invalid backend response");
      }

      // Normalise — ensure all fields GuidanceScreen expects are present
      return {
        session_id:     data.session_id     || sessionId.current,
        turn_id:        data.turn_id        || "UNKNOWN",
        risk_level:     data.risk_level     || "LOW",
        risk_score:     data.risk_score     ?? 0,
        response_steps: data.response_steps || [],
        action_plan:    data.action_plan    || {},
        fam_result:     data.fam_result     || {},
        echo_result:    data.echo_result    || {},
        voice_text:     data.voice_text     || "",
        dispatch_status: data.dispatch_status || "NONE",
        audit_id:       data.audit_id       || "",
      };

    } catch (err) {
      console.error("[AURA] API error:", err);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    process,
    startSession,
    loading,
    error,
    sessionId: sessionId.current,
  };
}