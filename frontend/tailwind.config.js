/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        slatebg: '#09121f',
        panel: '#0f1b2d',
        card: '#152238',
        accent: '#19c0a6',
        accent2: '#2ea8ff',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(46,168,255,.15), 0 8px 30px rgba(6,24,44,.35)',
      },
    },
  },
  plugins: [],
}
