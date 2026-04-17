/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        'as-black': '#000000',
        'as-white': '#ffffff',
        'as-body': '#4b4b4b',
        'as-muted': '#afafaf',
        'as-chip': '#efefef',
        'as-hover': '#e2e2e2',
        // Theme-switcher design tokens (resolved via CSS variables)
        'gray-700': 'var(--ds-gray-700)',
        'gray-1000': 'var(--ds-gray-1000)',
        'shadow': 'var(--ds-shadow)',
      },
      boxShadow: {
        card: 'rgba(0,0,0,0.12) 0px 4px 16px 0px',
        'card-md': 'rgba(0,0,0,0.16) 0px 4px 16px 0px',
      },
      borderRadius: {
        pill: '999px',
      },
    },
  },
  plugins: [],
}
