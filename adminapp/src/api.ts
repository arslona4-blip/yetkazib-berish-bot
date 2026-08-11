const AUTH_KEY = 'baraka-admin-auth-v1'

export type AuthState = {
  mode: 'tg' | 'pin'
  initData?: string
  pin?: string
  adminId?: number
}

export function loadAuth(): AuthState | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    return raw ? (JSON.parse(raw) as AuthState) : null
  } catch {
    return null
  }
}

export function saveAuth(auth: AuthState) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth))
}

export function clearAuth() {
  localStorage.removeItem(AUTH_KEY)
}

function headers(auth: AuthState | null): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (!auth) return h
  if (auth.mode === 'tg' && auth.initData) {
    h['X-Telegram-Init-Data'] = auth.initData
  } else if (auth.mode === 'pin' && auth.pin && auth.adminId) {
    h['X-Admin-Pin'] = auth.pin
    h['X-Admin-Id'] = String(auth.adminId)
  }
  return h
}

async function req<T>(
  path: string,
  auth: AuthState | null,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { ...headers(auth), ...(init?.headers || {}) },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  me: (auth: AuthState | null) =>
    req<{ ok: boolean; admin_id: number; shop_name: string }>('/api/admin/me', auth),
  stats: (auth: AuthState | null) =>
    req<import('./types').StatsPayload & { ok: boolean }>('/api/admin/stats', auth),
  orders: (auth: AuthState | null, status: string) =>
    req<{ ok: boolean; orders: import('./types').Order[] }>(
      `/api/admin/orders?status=${encodeURIComponent(status)}`,
      auth,
    ),
  setStatus: (auth: AuthState | null, orderId: number, status: string) =>
    req<{ ok: boolean; order: import('./types').Order }>(
      `/api/admin/orders/${orderId}/status`,
      auth,
      { method: 'POST', body: JSON.stringify({ status }) },
    ),
  whSummary: (auth: AuthState | null) =>
    req<Record<string, number> & { ok: boolean }>(
      '/api/admin/warehouse/summary',
      auth,
    ),
  whCategories: (auth: AuthState | null) =>
    req<{ ok: boolean; categories: import('./types').Category[] }>(
      '/api/admin/warehouse/categories',
      auth,
    ),
  whProducts: (auth: AuthState | null, categoryId?: number, lowOnly?: boolean) => {
    const q = new URLSearchParams()
    if (categoryId !== undefined) q.set('category_id', String(categoryId))
    if (lowOnly) q.set('low_only', '1')
    return req<{ ok: boolean; products: import('./types').Product[] }>(
      `/api/admin/warehouse/products?${q}`,
      auth,
    )
  },
  whMoves: (auth: AuthState | null) =>
    req<{ ok: boolean; movements: import('./types').Movement[] }>(
      '/api/admin/warehouse/movements?limit=50',
      auth,
    ),
  whStock: (
    auth: AuthState | null,
    body: {
      product_id: number
      mode: string
      qty: number
      delta?: number
      note?: string
    },
  ) =>
    req<{ ok: boolean; stock: number; name: string }>(
      '/api/admin/warehouse/stock',
      auth,
      { method: 'POST', body: JSON.stringify(body) },
    ),
  products: (auth: AuthState | null) =>
    req<{ ok: boolean; products: import('./types').Product[] }>(
      '/api/admin/products',
      auth,
    ),
}
