/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      "./src/**/*.{js,jsx,ts,tsx}",  // adjust this based on your project structure
    ],
    theme: {
    extend: {
        fontFamily: {
        sans: ['Ubuntu', 'sans-serif'],
      },
    },
  },
    plugins: [],
  }