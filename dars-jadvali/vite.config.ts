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
        name: 'Jadval',
        short_name: 'Jadval',
        description: 'Professional maktab dars jadvali — 9 dars, budilnik',
        theme_color: '#0a1c2e',
        background_color: '#e7eef6',
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
