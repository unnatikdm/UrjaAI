import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/api/': 'http://localhost:8000',
            '/auth/': 'http://localhost:8000',
            '/predict': 'http://localhost:8000',
            '/recommendations': 'http://localhost:8000',
            '/explain': 'http://localhost:8000',
            '/whatif': 'http://localhost:8000',
            '/buildings': 'http://localhost:8000',
            '/ingest/': 'http://localhost:8000',
            '/carbon-impact': 'http://localhost:8000',
            '/weather': 'http://localhost:8000',
            '/weather-alerts': 'http://localhost:8000',
            '/badges': 'http://localhost:8000',
            '/stats': 'http://localhost:8000',
            '/carbon-forecast': 'http://localhost:8000',
            '/optimize': 'http://localhost:8000',
            '/rag/': 'http://localhost:8000',
            '/enhanced/': 'http://localhost:8000',
        },
    },
})

