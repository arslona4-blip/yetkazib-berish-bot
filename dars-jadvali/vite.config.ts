import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/jadval/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Dars Jadvali',
        short_name: 'Jadval',
        description: 'Maktab o‘quvchilari uchun dars jadvali',
        theme_color: '#dce7f2',
        background_color: '#dce7f2',
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
