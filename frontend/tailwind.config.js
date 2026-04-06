/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pmpr: {
          green: '#1a3a2a',   // Verde Militar
          gold: '#c5a059',    // Dourado Sutil
          light: '#f8f9fa',   // Fundo claro
          dark: '#111827',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
