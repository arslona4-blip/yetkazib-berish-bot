import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/ingliz/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Ingliz',
        short_name: 'Ingliz',
        description: 'Ingliz tilini o‘rganish — so‘zlar, gaplar va mashqlar',
        theme_color: '#072a2e',
        background_color: '#072a2e',
        display: 'standalone',
        orientation: 'portrait',
        lang: 'uz',
        start_url: '/ingliz/',
        scope: '/ingliz/',
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
