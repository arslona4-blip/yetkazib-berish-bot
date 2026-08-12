import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/kichkintoy/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Kichkintoy AI',
        short_name: 'Kichkintoy',
        description: 'Bolalar uchun ertak-video generator',
        theme_color: '#ff7eb6',
        background_color: '#fff7fb',
        display: 'standalone',
        orientation: 'portrait',
        lang: 'uz',
        start_url: '/kichkintoy/',
        scope: '/kichkintoy/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],
})
