import { api, type AuthState } from './api'

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  const out = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i)
  return out
}

/** True only when running inside Telegram's WebView — not Chrome with telegram-web-app.js loaded. */
export function isLikelyTelegramWebView(): boolean {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent || ''
  if (/Telegram/i.test(ua)) return true
  const tw = (
    window as unknown as {
      Telegram?: { WebApp?: { initData?: string; platform?: string } }
    }
  ).Telegram?.WebApp
  // script always injects Telegram.WebApp; only real Mini App has initData
  if (tw?.initData && tw.initData.length > 0) return true
  const platform = (tw?.platform || '').toLowerCase()
  if (platform === 'android' || platform === 'ios' || platform === 'tdesktop') {
    // platform is set even outside Telegram sometimes — only block with initData
  }
  return false
}

export async function enableAdminPush(auth: AuthState): Promise<boolean> {
  if (typeof window === 'undefined') return false

  if (isLikelyTelegramWebView()) {
    throw new Error(
      'Telegram ichida Push ishlamaydi. Adminni Chrome da oching: ⋮ → Brauzerda ochish, keyin Push ni bosing',
    )
  }

  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    throw new Error(
      'Bu brauzer Push ni qo‘llab-quvvatlamaydi. Android Chrome yoki PWA kerak',
    )
  }
  if (!('Notification' in window)) {
    throw new Error('Bildirishnoma API yo‘q — Chrome da oching')
  }
  if (!window.isSecureContext) {
    throw new Error('Push uchun HTTPS kerak')
  }

  const { publicKey } = await api.pushVapid(auth)
  if (!publicKey) throw new Error('VAPID kalit topilmadi (server)')

  let permission = Notification.permission
  if (permission === 'default') {
    permission = await Notification.requestPermission()
  }
  if (permission === 'denied') {
    throw new Error(
      'Ruxsat rad etilgan. Chrome → 🔒/ℹ️ sayt → Bildirishnomalar → Ruxsat, keyin Push ni qayta bosing',
    )
  }
  if (permission !== 'granted') {
    throw new Error('Bildirishnoma ruxsati berilmadi')
  }

  // Wait for SW (vite-plugin-pwa) — ready can hang if never registered
  let registration = await navigator.serviceWorker.getRegistration()
  if (!registration) {
    try {
      registration = await navigator.serviceWorker.register('/admin/sw.js', {
        scope: '/admin/',
      })
    } catch (e) {
      throw new Error(
        e instanceof Error
          ? `Service Worker: ${e.message}`
          : 'Service Worker ro‘yxatdan o‘tmadi',
      )
    }
  }
  registration = await navigator.serviceWorker.ready

  let subscription = await registration.pushManager.getSubscription()
  if (subscription) {
    try {
      await subscription.unsubscribe()
    } catch {
      /* ignore */
    }
    subscription = null
  }
  try {
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey) as BufferSource,
    })
  } catch (e) {
    throw new Error(
      e instanceof Error
        ? `Subscribe xato: ${e.message}`
        : 'Push subscribe bo‘lmadi',
    )
  }

  const json = subscription.toJSON()
  const endpoint = json.endpoint || subscription.endpoint
  const p256dh = json.keys?.p256dh
  const authKey = json.keys?.auth
  if (!endpoint || !p256dh || !authKey) {
    throw new Error('Subscription kalitlari to‘liq emas')
  }

  await api.pushSubscribe(auth, {
    endpoint,
    keys: { p256dh, auth: authKey },
  })
  return true
}
