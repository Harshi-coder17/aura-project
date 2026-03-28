// frontend/src/components/Toast.jsx
import { useEffect, useState } from "react";

export default function Toast({ message }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!message) { setVisible(false); return; }
    setVisible(true);
  }, [message]);

  if (!visible || !message) return null;

  return (
    <div
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999]
                 bg-navy text-white px-6 py-3 rounded-3xl text-sm
                 font-medium shadow-2xl animate-toast max-w-xs text-center
                 pointer-events-none"
    >
      {message}
    </div>
  );
}