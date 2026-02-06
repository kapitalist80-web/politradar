/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        swiss: {
          red: "#D52B1E",
          dark: "#8B0000",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
