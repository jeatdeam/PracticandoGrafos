import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Las llamadas a /api se redirigen al backend de FastAPI
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
