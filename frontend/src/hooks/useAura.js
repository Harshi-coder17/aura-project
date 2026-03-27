import { useState, useRef, useCallback } from "react";
import BACKEND_URL from "../config";

export default function useAura() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sessionId = useRef(crypto.randomUUID());
  const turnRef = useRef(1);

  // 🔹 SESSION INIT (SAFE FALLBACK)
  const startSession = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/session/start`, {
        method: "POST",
      });

      if (!res.ok) throw new Error();

      const data = await res.json();

      if (data?.session_id) {
        sessionId.current = data.session_id;
      }
    } catch {
      // fallback stays
      sessionId.current = crypto.randomUUID();
      console.warn("[AURA] Using fallback session");
    }
  }, []);

  //  MAIN PROCESS FUNCTION 
  const process = useCallback(async (text, mode, userId = null) => {
    setLoading(true);
    setError(null);

    try {
      //  FULL PAYLOAD 
      const payload = {
        session_id: sessionId.current,
        user_id: mode === "personal" ? (userId || "user_demo") : null,
        mode: mode,
        text: text,
        turn_number: turnRef.current++,
      };

      console.log("🚀 SENDING TO BACKEND:", payload);

      const res = await fetch(`${BACKEND_URL}/api/v1/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({
          detail: "Server error",
        }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();

      console.log("BACKEND RESPONSE:", data);

      // RESPONSE HARDENING 
      if (!data || typeof data !== "object") {
        throw new Error("Invalid backend response");
      }

      //  Ensure required fields exist (fallback-safe)
      return {
        session_id: data.session_id || sessionId.current,
        turn_id: data.turn_id || "UNKNOWN",
        risk_level: data.risk_level || "LOW",
        risk_score: data.risk_score ?? 0,
        response_steps: data.response_steps || [],
        action_plan: data.action_plan || {},
        fam_result: data.fam_result || {},
        echo_result: data.echo_result || {},
        voice_text: data.voice_text || "",
      };

    } catch (err) {
      console.error("❌ API ERROR:", err);
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