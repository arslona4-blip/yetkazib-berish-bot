import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/taklifnoma/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Taklifnoma',
        short_name: 'Taklifnoma',
        description: 'Chiroyli taklifnoma yasash studiyasi',
        theme_color: '#12483A',
        background_color: '#0B2A22',
        display: 'standalone',
        orientation: 'portrait',
        lang: 'uz',
        start_url: '/taklifnoma/',
        scope: '/taklifnoma/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],
})
