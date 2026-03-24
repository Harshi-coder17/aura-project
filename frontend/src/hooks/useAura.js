import { useState, useRef, useCallback } from "react";
import BACKEND_URL from "../config";

export default function useAura() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const sessionId = useRef(crypto.randomUUID());
  const turnRef = useRef(1);

  const startSession = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/session/start`, { method: "POST" });
      const data = await res.json();
      sessionId.current = data.session_id;
    } catch {
      sessionId.current = crypto.randomUUID();
    }
  }, []);

  const process = useCallback(async (text, mode, userId = null) => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        session_id: sessionId.current,
        user_id: mode === "personal" ? (userId || "user_demo") : null,
        mode: mode,
        text: text,
        turn_number: turnRef.current++,
      };
      const res = await fetch(`${BACKEND_URL}/api/v1/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Server error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { process, startSession, loading, error, sessionId: sessionId.current };
}
