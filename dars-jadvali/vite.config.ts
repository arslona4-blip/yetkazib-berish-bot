import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/jadval/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: [
        'favicon.png',
        'apple-touch-icon.png',
        'brand-dars-jadvali.png',
        'brand-dars-jadvali.webp',
        'icon-192-v3.png',
        'icon-512-v3.png',
        'icon-512-maskable-v3.png',
      ],
      manifest: {
        id: '/jadval/?v=3',
        name: 'Dars Jadvali',
        short_name: 'Dars Jadvali',
        description: 'Maktab dars jadvali — zamonaviy o‘quvchi ilovasi',
        theme_color: '#0b4f8a',
        background_color: '#0b4f8a',
        display: 'standalone',
        orientation: 'any',
        lang: 'uz',
        start_url: '/jadval/?source=pwa',
        scope: '/jadval/',
        icons: [
          {
            src: 'icon-192-v3.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: 'icon-512-v3.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: 'icon-512-maskable-v3.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        // yangi ikonkalar darhol yangilansin
        cleanupOutdatedCaches: true,
      },
    }),
  ],
})
