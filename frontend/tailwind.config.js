/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: "#0A0F1C",
        electric: "#3B82F6",
      },
    },
  },
  plugins: [],
}
