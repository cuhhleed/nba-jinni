/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Russo One", "sans-serif"],
        light: ["DM Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
}
