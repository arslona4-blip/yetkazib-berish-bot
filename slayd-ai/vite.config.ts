import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/slayd/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'Slayd Studio',
        short_name: 'Slayd',
        description: 'Lovable uslubida AI slayd studiyasi',
        theme_color: '#111827',
        background_color: '#0b1020',
        display: 'standalone',
        lang: 'uz',
        start_url: '/slayd/',
        scope: '/slayd/',
        icons: [
          { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],
})
