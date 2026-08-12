import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/arduino/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Arduino Darslik',
        short_name: 'Arduino',
        description: 'Arduino asoslari — telefon va PC uchun darslik',
        theme_color: '#0c1412',
        background_color: '#0c1412',
        display: 'standalone',
        orientation: 'any',
        lang: 'uz',
        start_url: '/arduino/',
        scope: '/arduino/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: 'pwa-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
    }),
  ],
})
