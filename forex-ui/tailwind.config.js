/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0f172a",       // background principal
        card: "#1e293b",     // cartes
        accent: "#22c55e",   // vert trading
        danger: "#ef4444",   // rouge sell
      },
    },
  },
  plugins: [],
}