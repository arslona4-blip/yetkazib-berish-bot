import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['@vladmandic/face-api'],
  },
  server: {
    host: true,
    port: 5177,
  },
  build: {
    chunkSizeWarningLimit: 1600,
  },
})
