/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'arise-purple': '#6B46C1',
        'arise-blue': '#1E40AF',
        'arise-gold': '#F59E0B',
        'arise-red': '#DC2626',
        'arise-green': '#059669',
        'arise-dark': '#111827',
        'arise-gray': '#374151',
      },
      fontFamily: {
        'game': ['Orbitron', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 2s infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #6B46C1, 0 0 10px #6B46C1, 0 0 15px #6B46C1' },
          '100%': { boxShadow: '0 0 10px #6B46C1, 0 0 20px #6B46C1, 0 0 30px #6B46C1' },
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'game-bg': "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)",
      },
    },
  },
  plugins: [],
}