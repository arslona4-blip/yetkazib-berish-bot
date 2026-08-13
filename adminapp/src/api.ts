const AUTH_KEY = 'baraka-admin-auth-v2'

export type AuthState = {
  mode: 'tg' | 'pin' | 'session'
  initData?: string
  pin?: string
  adminId?: number
  session?: string
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
  try {
    localStorage.removeItem('baraka-admin-auth-v1')
  } catch {
    /* ignore */
  }
}

function headers(auth: AuthState | null): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (!auth) return h
  if (auth.mode === 'tg' && auth.initData) {
    h['X-Telegram-Init-Data'] = auth.initData
  } else if (auth.mode === 'session' && auth.session) {
    h['X-Admin-Session'] = auth.session
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
  login: (adminId: number, code: string) =>
    req<{
      ok: boolean
      admin_id: number
      session: string
      shop_name: string
    }>('/api/admin/login', null, {
      method: 'POST',
      body: JSON.stringify({ admin_id: adminId, code }),
    }),
  logout: (auth: AuthState | null) =>
    req<{ ok: boolean }>('/api/admin/logout', auth, { method: 'POST' }),
  me: (auth: AuthState | null) =>
    req<{ ok: boolean; admin_id: number; shop_name: string }>('/api/admin/me', auth),
  stats: (auth: AuthState | null) =>
    req<import('./types').StatsPayload & { ok: boolean }>('/api/admin/stats', auth),
  orders: (auth: AuthState | null, status: string, q = '') => {
    const params = new URLSearchParams({ status })
    if (q.trim()) params.set('q', q.trim())
    return req<{ ok: boolean; orders: import('./types').Order[] }>(
      `/api/admin/orders?${params}`,
      auth,
    )
  },
  orderDetail: (auth: AuthState | null, orderId: number) =>
    req<{
      ok: boolean
      order: import('./types').Order
      items: import('./types').OrderItem[]
    }>(`/api/admin/orders/${orderId}`, auth),
  setStatus: (auth: AuthState | null, orderId: number, status: string) =>
    req<{ ok: boolean; order: import('./types').Order }>(
      `/api/admin/orders/${orderId}/status`,
      auth,
      { method: 'POST', body: JSON.stringify({ status }) },
    ),
  setPayment: (
    auth: AuthState | null,
    orderId: number,
    action: 'confirm' | 'reject',
  ) =>
    req<{ ok: boolean; order: import('./types').Order }>(
      `/api/admin/orders/${orderId}/payment`,
      auth,
      { method: 'POST', body: JSON.stringify({ action }) },
    ),
  deleteOrder: (auth: AuthState | null, orderId: number) =>
    req<{ ok: boolean; deleted: number }>(`/api/admin/orders/${orderId}`, auth, {
      method: 'DELETE',
    }),
  posSale: (
    auth: AuthState | null,
    body: {
      items: { product_id: number; quantity: number }[]
      payment: 'cash' | 'card'
      customer_name?: string
      phone?: string
      note?: string
      promo_code?: string
      contact_id?: number
    },
  ) =>
    req<{
      ok: boolean
      order: import('./types').Order
      total: number
      discount: number
      subtotal: number
      payment: string
      contact_id: number | null
    }>('/api/admin/pos/sale', auth, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  promos: (auth: AuthState | null) =>
    req<{ ok: boolean; promos: import('./types').Promo[] }>(
      '/api/admin/promos',
      auth,
    ),
  upsertPromo: (
    auth: AuthState | null,
    body: {
      code: string
      discount_percent?: number
      discount_amount?: number
      min_order?: number
      is_active?: boolean
    },
  ) =>
    req<{ ok: boolean; promo: import('./types').Promo }>(
      '/api/admin/promos',
      auth,
      { method: 'POST', body: JSON.stringify(body) },
    ),
  patchPromo: (
    auth: AuthState | null,
    code: string,
    body: Partial<import('./types').Promo>,
  ) =>
    req<{ ok: boolean; promo: import('./types').Promo }>(
      `/api/admin/promos/${encodeURIComponent(code)}`,
      auth,
      { method: 'PATCH', body: JSON.stringify(body) },
    ),
  reports: (auth: AuthState | null, from: string, to: string) =>
    req<{
      ok: boolean
      report: import('./types').RangeReport
      warehouse: import('./types').StatsPayload['warehouse']
    }>(`/api/admin/reports?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`, auth),
  categories: (auth: AuthState | null) =>
    req<{ ok: boolean; categories: import('./types').CatalogCategory[] }>(
      '/api/admin/categories',
      auth,
    ),
  createCategory: (auth: AuthState | null, name: string) =>
    req<{ ok: boolean; id: number; name: string }>(
      '/api/admin/categories',
      auth,
      { method: 'POST', body: JSON.stringify({ name }) },
    ),
  whCategories: (auth: AuthState | null, lowOnly?: boolean) => {
    const q = new URLSearchParams()
    if (lowOnly) q.set('low_only', '1')
    return req<{ ok: boolean; categories: import('./types').Category[] }>(
      `/api/admin/warehouse/categories?${q}`,
      auth,
    )
  },
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
  createProduct: (
    auth: AuthState | null,
    body: {
      name: string
      price: number
      category_id?: number
      barcode?: string
      description?: string
      stock?: number
    },
  ) =>
    req<{ ok: boolean; product: import('./types').Product }>(
      '/api/admin/products',
      auth,
      { method: 'POST', body: JSON.stringify(body) },
    ),
  productByBarcode: (auth: AuthState | null, code: string) =>
    req<{ ok: boolean; product: import('./types').Product }>(
      `/api/admin/products/barcode/${encodeURIComponent(code)}`,
      auth,
    ),
  patchProduct: (
    auth: AuthState | null,
    productId: number,
    body: {
      price?: number
      is_active?: boolean
      name?: string
      barcode?: string
      category_id?: number | null
      description?: string
      stock?: number
    },
  ) =>
    req<{ ok: boolean; product: import('./types').Product }>(
      `/api/admin/products/${productId}`,
      auth,
      { method: 'PATCH', body: JSON.stringify(body) },
    ),
  broadcast: (auth: AuthState | null, text: string) =>
    req<{ ok: boolean; sent: number; failed: number; total: number }>(
      '/api/admin/broadcast',
      auth,
      { method: 'POST', body: JSON.stringify({ text }) },
    ),
  exportCsv: async (auth: AuthState | null) => {
    const res = await fetch('/api/admin/products/export', {
      headers: headers(auth),
    })
    if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`)
    return res.text()
  },
  importCsv: (auth: AuthState | null, csv: string) =>
    req<{ ok: boolean; imported: number }>('/api/admin/products/import', auth, {
      method: 'POST',
      body: JSON.stringify({ csv }),
    }),
  contacts: (auth: AuthState | null) =>
    req<{ ok: boolean; contacts: import('./types').Contact[] }>(
      '/api/admin/contacts',
      auth,
    ),
  createContact: (
    auth: AuthState | null,
    body: { name: string; phone?: string; note?: string },
  ) =>
    req<{ ok: boolean; contact: import('./types').Contact }>(
      '/api/admin/contacts',
      auth,
      { method: 'POST', body: JSON.stringify(body) },
    ),
  updateContact: (
    auth: AuthState | null,
    id: number,
    body: { name?: string; phone?: string; note?: string },
  ) =>
    req<{ ok: boolean; contact: import('./types').Contact }>(
      `/api/admin/contacts/${id}`,
      auth,
      { method: 'PATCH', body: JSON.stringify(body) },
    ),
}
