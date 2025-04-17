import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 🌍 URL backend (Render en prod / localhost en dev)
const backendUrl = process.env.BACKEND_URL || "http://localhost:5002"

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/historique': backendUrl,
      '/performance': backendUrl,
      '/start_bot': backendUrl,
      '/logs': backendUrl,
      '/rapport_ia': backendUrl,
    },
  },
})
