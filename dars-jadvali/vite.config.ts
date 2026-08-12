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
        name: '32-GR Dars Jadvali',
        short_name: 'Jadval',
        description: '32-GR Online Robototexnika — o‘quvchilar uchun dars jadvali',
        theme_color: '#0f1a17',
        background_color: '#0f1a17',
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
