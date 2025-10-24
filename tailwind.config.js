/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './core/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0B5FFF',
          50: '#E6F0FF',
          100: '#CCE1FF',
          200: '#99C3FF',
          300: '#66A5FF',
          400: '#3387FF',
          500: '#0B5FFF',
          600: '#0A4EF2',
          700: '#083FCC',
          800: '#062FA6',
          900: '#041F80',
        },
      },
    },
  },
  plugins: [],
}
