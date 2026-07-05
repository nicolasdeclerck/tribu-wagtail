/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./tribu/templates/**/*.html",
    "./core/templates/**/*.html",
    "./home/templates/**/*.html",
    "./projets/templates/**/*.html",
    "./stages/templates/**/*.html",
    "./compagnie/templates/**/*.html",
    "./reseaux/templates/**/*.html",
    "./contact/templates/**/*.html",
    "./search/templates/**/*.html",
    "./core/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Couleur secondaire de la marque : le jaune du logo « la tribu d'Oya ».
        secondary: "#f3d159",
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("@tailwindcss/forms"),
  ],
};
