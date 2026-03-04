import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/auth': 'http://localhost:8000',
            '/predict': 'http://localhost:8000',
            '/recommendations': 'http://localhost:8000',
            '/explain': 'http://localhost:8000',
            '/whatif': 'http://localhost:8000',
            '/buildings': 'http://localhost:8000',
            '/ingest': 'http://localhost:8000',
        },
    },
})

