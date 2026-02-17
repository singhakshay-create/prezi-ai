/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'mckinsey-blue': '#003399',
        'light-blue': '#00b0f0',
      }
    },
  },
  plugins: [],
}
