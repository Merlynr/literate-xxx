/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#fbf7ef',
          100: '#f3ead8',
          200: '#eef3ee',
        },
        brand: {
          900: '#10291b',
          700: '#1f5d3a',
          500: '#2d7d4d',
        },
        gold: {
          600: '#b98b2a',
          400: '#d9b563',
        },
      },
      fontFamily: {
        sans: ['"PingFang SC"', '"Microsoft YaHei"', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
