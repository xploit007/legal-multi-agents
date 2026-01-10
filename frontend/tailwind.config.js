/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'legal-primary': '#1a365d',
        'legal-secondary': '#2c5282',
        'legal-accent': '#3182ce',
        'strategist': '#3182ce',
        'precedent': '#805ad5',
        'adversarial': '#e53e3e',
        'moderator': '#38a169',
      },
      fontFamily: {
        'legal': ['Georgia', 'Times New Roman', 'serif'],
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'thinking': 'thinking 1.5s ease-in-out infinite',
      },
      keyframes: {
        thinking: {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
