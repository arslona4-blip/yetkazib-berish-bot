import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/baxtnoma/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Baxtnoma',
        short_name: 'Baxtnoma',
        description: 'Chiroyli baxtnoma va tabrik yasash studiyasi',
        theme_color: '#4A1424',
        background_color: '#F2EEE8',
        display: 'standalone',
        orientation: 'portrait',
        lang: 'uz',
        start_url: '/baxtnoma/',
        scope: '/baxtnoma/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],
})
