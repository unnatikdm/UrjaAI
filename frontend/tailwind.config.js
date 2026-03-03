/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#22c55e',   // green-500
                    dark: '#16a34a',      // green-600
                    light: '#86efac',     // green-300
                    xlight: '#dcfce7',    // green-100
                },
                beige: {
                    DEFAULT: '#f5f0e8',
                    dark: '#ede7d9',
                    light: '#faf8f4',
                },
                surface: {
                    DEFAULT: '#ffffff',
                    elevated: '#f9fffe',
                    muted: '#f0fdf4',     // green-50
                },
                ink: {
                    DEFAULT: '#1a2e1e',   // very dark green
                    soft: '#3d5a40',
                    muted: '#6b8f6e',
                    faint: '#9cb89e',
                },
                border: {
                    DEFAULT: '#c8e6cc',
                    subtle: '#e8f5ea',
                    strong: '#a3d4a8',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
