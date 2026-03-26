/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy:     "#0A1628",
        electric: "#1E90FF",
        teal:     "#00CED1",
        danger:   "#E74C3C",
        safe:     "#2ECC71",
        amber:    "#F39C12",
        personal: "#1E90FF",
        stranger: "#636e72",
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4,0,0.6,1) infinite",
        "fade-in":    "fade-in 0.3s ease-out",
      },
      keyframes: {
        "pulse-ring": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(231,76,60,0.6)" },
          "70%":       { boxShadow: "0 0 0 30px rgba(231,76,60,0)" },
        },
        "fade-in": {
          from: { opacity: 0, transform: "translateY(8px)" },
          to:   { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
}


