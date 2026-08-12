import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/jadval/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.png', 'brand-dars-jadvali.png', 'brand-dars-jadvali.webp'],
      manifest: {
        name: 'Dars Jadvali',
        short_name: 'Jadval',
        description: 'Maktab dars jadvali — zamonaviy o‘quvchi ilovasi',
        theme_color: '#0b4f8a',
        background_color: '#eef2f7',
        display: 'standalone',
        orientation: 'any',
        lang: 'uz',
        start_url: '/jadval/',
        scope: '/jadval/',
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
