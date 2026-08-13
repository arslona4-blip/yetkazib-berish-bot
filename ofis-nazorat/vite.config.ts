import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  plugins: [react()],
  optimizeDeps: {
    exclude: ['@vladmandic/face-api'],
  },
  server: {
    host: '127.0.0.1',
    port: 5177,
    strictPort: true,
  },
  build: {
    chunkSizeWarningLimit: 1600,
  },
})
