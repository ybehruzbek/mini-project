/** @type {import('tailwindcss').Config} */
module.exports = {
  // index.html va app.js ichidagi barcha class nomlarini skanerlaydi
  content: ['./index.html', './app.js'],
  // CDN'ning standart xatti-harakati bilan mos: dark: utilitalari OS mavzusiga bog'lanadi.
  // Ilovaning qo'lbola dark rejimi CSS o'zgaruvchilari (body.dark-theme) orqali ishlaydi.
  darkMode: 'media',
  theme: {
    extend: {},
  },
  plugins: [],
};
