/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        dark: {
          bg: '#1a1a2e',
          surface: '#16213e',
          card: '#0f3460',
          accent: '#00d9ff',
        }
      },
      minHeight: {
        'touch': '44px', // Touch-friendly minimum height
      },
      minWidth: {
        'touch': '44px', // Touch-friendly minimum width
      }
    },
  },
  plugins: [],
}
