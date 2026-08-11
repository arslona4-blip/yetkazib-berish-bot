import { useEffect, useMemo, useState } from 'react'
import {
  api,
  clearAuth,
  loadAuth,
  saveAuth,
  type AuthState,
} from './api'
import type {
  Category,
  Movement,
  Order,
  OrderItem,
  Product,
  StatsPayload,
  Tab,
} from './types'
import './styles.css'

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string
        ready?: () => void
        expand?: () => void
        themeParams?: Record<string, string>
      }
    }
  }
}

const REASON: Record<string, string> = {
  sale: '🛒 Sotuv',
  in: '📥 Kirim',
  out: '📤 Chiqim',
  inventory: '📋 Inventar',
  adjust: '✏️ Tuzatish',
}

const ORDER_FILTERS: [string, string][] = [
  ['new', 'Yangi'],
  ['active', 'Faol'],
  ['delivered', 'Yetkazilgan'],
  ['cancelled', 'Bekor'],
]

function money(n: number) {
  return `${Number(n || 0).toLocaleString('uz-UZ')} so‘m`
}

export default function App() {
  const [auth, setAuth] = useState<AuthState | null>(() => loadAuth())
  const [tab, setTab] = useState<Tab>('dash')
  const [shop, setShop] = useState('Admin')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [lastSync, setLastSync] = useState('')
  const [stats, setStats] = useState<StatsPayload | null>(null)
  const [orderStatus, setOrderStatus] = useState('new')
  const [orderQuery, setOrderQuery] = useState('')
  const [orders, setOrders] = useState<Order[]>([])
  const [payments, setPayments] = useState<Order[]>([])
  const [openOrderId, setOpenOrderId] = useState<number | null>(null)
  const [orderItems, setOrderItems] = useState<OrderItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [catalog, setCatalog] = useState<Product[]>([])
  const [selectedCat, setSelectedCat] = useState<number | 'all'>('all')
  const [lowOnly, setLowOnly] = useState(false)
  const [moves, setMoves] = useState<Movement[]>([])
  const [stockForm, setStockForm] = useState({
    product_id: 0,
    mode: 'in',
    qty: 1,
    note: '',
  })
  const [pinForm, setPinForm] = useState({ adminId: '', pin: '' })
  const [priceEdit, setPriceEdit] = useState<Record<number, string>>({})

  const tgInit = window.Telegram?.WebApp?.initData || ''

  useEffect(() => {
    window.Telegram?.WebApp?.ready?.()
    window.Telegram?.WebApp?.expand?.()
  }, [])

  useEffect(() => {
    if (tgInit && (!auth || auth.mode !== 'tg')) {
      const next: AuthState = { mode: 'tg', initData: tgInit }
      saveAuth(next)
      setAuth(next)
    }
  }, [tgInit]) // eslint-disable-line react-hooks/exhaustive-deps

  async function bootstrap(a: AuthState) {
    setBusy(true)
    setError('')
    try {
      const me = await api.me(a)
      setShop(me.shop_name || 'Admin')
      saveAuth(a)
      setAuth(a)
      await refreshAll(a)
    } catch (e) {
      clearAuth()
      setAuth(null)
      setError(e instanceof Error ? e.message : 'Kirish xato')
    } finally {
      setBusy(false)
    }
  }

  async function refreshAll(a: AuthState | null = auth, silent = false) {
    if (!a) return
    if (!silent) setBusy(true)
    setError('')
    try {
      const [st, or, pay, cats, prods, mv, cat] = await Promise.all([
        api.stats(a),
        api.orders(a, orderStatus, orderQuery),
        api.orders(a, 'payments'),
        api.whCategories(a, lowOnly),
        api.whProducts(a, selectedCat === 'all' ? undefined : selectedCat, lowOnly),
        api.whMoves(a),
        api.products(a),
      ])
      setStats(st)
      setOrders(or.orders)
      setPayments(pay.orders)
      setCategories(cats.categories)
      setProducts(prods.products)
      setMoves(mv.movements)
      setCatalog(cat.products)
      setLastSync(new Date().toLocaleTimeString('uz-UZ'))
    } catch (e) {
      if (!silent) setError(e instanceof Error ? e.message : 'Yuklash xato')
    } finally {
      if (!silent) setBusy(false)
    }
  }

  useEffect(() => {
    if (auth) void bootstrap(auth)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!auth) return
    const id = window.setInterval(() => {
      void refreshAll(auth, true)
    }, 20000)
    return () => window.clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth, orderStatus, orderQuery, lowOnly, selectedCat])

  useEffect(() => {
    if (!auth) return
    void (async () => {
      try {
        const or = await api.orders(auth, orderStatus, orderQuery)
        setOrders(or.orders)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Buyurtmalar xato')
      }
    })()
  }, [orderStatus, orderQuery, auth])

  useEffect(() => {
    if (!auth) return
    void (async () => {
      try {
        const [cats, prods] = await Promise.all([
          api.whCategories(auth, lowOnly),
          api.whProducts(
            auth,
            selectedCat === 'all' ? undefined : selectedCat,
            lowOnly,
          ),
        ])
        setCategories(cats.categories)
        setProducts(prods.products)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Ombor xato')
      }
    })()
  }, [lowOnly, selectedCat, auth])

  const filteredProducts = useMemo(() => products, [products])

  async function changeStatus(orderId: number, status: string) {
    if (!auth) return
    setBusy(true)
    try {
      await api.setStatus(auth, orderId, status)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Status xato')
    } finally {
      setBusy(false)
    }
  }

  async function changePayment(orderId: number, action: 'confirm' | 'reject') {
    if (!auth) return
    setBusy(true)
    try {
      await api.setPayment(auth, orderId, action)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'To‘lov xato')
    } finally {
      setBusy(false)
    }
  }

  async function removeOrder(orderId: number) {
    if (!auth) return
    if (!window.confirm(`#${orderId} o‘chirilsinmi?`)) return
    setBusy(true)
    try {
      await api.deleteOrder(auth, orderId)
      setOpenOrderId(null)
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'O‘chirish xato')
    } finally {
      setBusy(false)
    }
  }

  async function toggleDetail(orderId: number) {
    if (!auth) return
    if (openOrderId === orderId) {
      setOpenOrderId(null)
      setOrderItems([])
      return
    }
    try {
      const detail = await api.orderDetail(auth, orderId)
      setOpenOrderId(orderId)
      setOrderItems(detail.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Tafsilot xato')
    }
  }

  async function submitStock() {
    if (!auth || !stockForm.product_id) return
    setBusy(true)
    try {
      await api.whStock(auth, {
        product_id: stockForm.product_id,
        mode: stockForm.mode,
        qty: Number(stockForm.qty),
        note: stockForm.note,
      })
      setStockForm((s) => ({ ...s, qty: 1, note: '' }))
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ombor xato')
    } finally {
      setBusy(false)
    }
  }

  async function quickIn(productId: number, qty: number) {
    if (!auth) return
    setBusy(true)
    try {
      await api.whStock(auth, {
        product_id: productId,
        mode: 'in',
        qty,
        note: 'Tezkor kirim',
      })
      await refreshAll(auth, true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kirim xato')
    } finally {
      setBusy(false)
    }
  }

  async function toggleProduct(p: Product) {
    if (!auth) return
    setBusy(true)
    try {
      await api.patchProduct(auth, p.id, { is_active: !p.is_active })
      const cat = await api.products(auth)
      setCatalog(cat.products)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mahsulot xato')
    } finally {
      setBusy(false)
    }
  }

  async function savePrice(p: Product) {
    if (!auth) return
    const raw = priceEdit[p.id]
    if (raw === undefined) return
    const price = Number(raw)
    if (!Number.isFinite(price) || price < 0) {
      setError('Narx noto‘g‘ri')
      return
    }
    setBusy(true)
    try {
      await api.patchProduct(auth, p.id, { price })
      setPriceEdit((s) => {
        const next = { ...s }
        delete next[p.id]
        return next
      })
      const cat = await api.products(auth)
      setCatalog(cat.products)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Narx xato')
    } finally {
      setBusy(false)
    }
  }

  function renderOrderCard(o: Order, showPay = false) {
    const open = openOrderId === o.id
    return (
      <article key={o.id} className="item">
        <button
          type="button"
          className="item-head"
          onClick={() => void toggleDetail(o.id)}
        >
          <div className="row-between">
            <h3>
              #{o.id} · {money(o.price)}
            </h3>
            <span className="badge">{o.status_label}</span>
          </div>
          <p>
            {o.phone || '—'} · {o.delivery_address || 'Manzil yo‘q'}
            {o.delivery_slot ? ` · ${o.delivery_slot}` : ''}
          </p>
          <div className="meta">
            <span className="badge warn">{o.payment_label}</span>
            <span className="muted-sm">{o.created_at}</span>
          </div>
        </button>

        {open ? (
          <div className="detail">
            {orderItems.length === 0 ? (
              <p className="muted-sm">Mahsulotlar yo‘q</p>
            ) : (
              <ul className="lines">
                {orderItems.map((it) => (
                  <li key={it.id}>
                    <span>
                      {it.product_name} × {it.quantity}
                    </span>
                    <span className="mono">{money(it.line_total)}</span>
                  </li>
                ))}
              </ul>
            )}
            {o.description ? <p className="note">{o.description}</p> : null}
          </div>
        ) : null}

        {showPay ? (
          <div className="actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void changePayment(o.id, 'confirm')}
            >
              Tasdiqlash
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void changePayment(o.id, 'reject')}
            >
              Rad etish
            </button>
          </div>
        ) : (
          <div className="actions">
            {['accepted', 'in_delivery', 'delivered', 'cancelled'].map((st) => (
              <button
                key={st}
                type="button"
                className="btn btn-ghost"
                onClick={() => void changeStatus(o.id, st)}
              >
                {st === 'accepted'
                  ? 'Qabul'
                  : st === 'in_delivery'
                    ? 'Yo‘lda'
                    : st === 'delivered'
                      ? 'Yetkazildi'
                      : 'Bekor'}
              </button>
            ))}
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void removeOrder(o.id)}
            >
              O‘chirish
            </button>
          </div>
        )}
      </article>
    )
  }

  if (!auth) {
    return (
      <div className="login">
        <div className="login-box">
          <div className="login-mark" aria-hidden />
          <h1>
            Admin <span style={{ color: 'var(--accent)' }}>Panel</span>
          </h1>
          <p>
            Professional boshqaruv: buyurtmalar, to‘lovlar, ombor va hisobotlar.
          </p>
          {tgInit ? (
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%', marginBottom: 12 }}
              onClick={() =>
                void bootstrap({ mode: 'tg', initData: tgInit })
              }
            >
              Telegram orqali kirish
            </button>
          ) : null}
          <div className="field">
            <label>Telegram Admin ID</label>
            <input
              value={pinForm.adminId}
              onChange={(e) =>
                setPinForm((s) => ({ ...s, adminId: e.target.value }))
              }
              placeholder="123456789"
              inputMode="numeric"
            />
          </div>
          <div className="field">
            <label>Admin PIN</label>
            <input
              type="password"
              value={pinForm.pin}
              onChange={(e) =>
                setPinForm((s) => ({ ...s, pin: e.target.value }))
              }
              placeholder="••••"
            />
          </div>
          {error ? <div className="error">{error}</div> : null}
          <button
            type="button"
            className="btn btn-primary"
            style={{ width: '100%' }}
            disabled={busy}
            onClick={() =>
              void bootstrap({
                mode: 'pin',
                pin: pinForm.pin,
                adminId: Number(pinForm.adminId),
              })
            }
          >
            Kirish
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={`app${busy ? ' busy' : ''}`}>
      <header className="top">
        <div>
          <h1 className="brand">
            {shop} <span>Admin</span>
          </h1>
          <p className="sub">
            Professional boshqaruv
            {lastSync ? ` · yangilandi ${lastSync}` : ''}
          </p>
        </div>
        <div className="actions top-actions">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => void refreshAll()}
          >
            Yangilash
          </button>
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => {
              clearAuth()
              setAuth(null)
            }}
          >
            Chiqish
          </button>
        </div>
      </header>

      {error ? <div className="error">{error}</div> : null}

      {tab === 'dash' && stats ? (
        <>
          <div className="grid grid-4">
            <button
              type="button"
              className="card clickable"
              onClick={() => {
                setOrderStatus('new')
                setTab('orders')
              }}
            >
              <div className="label">Yangi</div>
              <div className="value accent">{stats.stats.new_orders}</div>
            </button>
            <button
              type="button"
              className="card clickable"
              onClick={() => {
                setOrderStatus('active')
                setTab('orders')
              }}
            >
              <div className="label">Faol</div>
              <div className="value">{stats.stats.active_orders}</div>
            </button>
            <button
              type="button"
              className="card clickable"
              onClick={() => setTab('payments')}
            >
              <div className="label">Karta kutmoqda</div>
              <div className="value warn">{stats.payments_waiting}</div>
            </button>
            <button
              type="button"
              className="card clickable"
              onClick={() => {
                setLowOnly(true)
                setTab('warehouse')
              }}
            >
              <div className="label">Kam qoldiq</div>
              <div className="value warn">{stats.warehouse.low_stock}</div>
            </button>
          </div>

          <div className="section grid">
            <div className="card">
              <div className="label">Bugun savdo</div>
              <div className="value mono">{money(stats.daily.revenue)}</div>
              <p className="muted-sm">{stats.daily.orders_count} buyurtma</p>
            </div>
            <div className="card">
              <div className="label">To‘langan / kutayotgan</div>
              <div className="value" style={{ fontSize: '1rem' }}>
                {money(stats.daily.paid_sum)}
                <span className="muted-sm"> / </span>
                {money(stats.daily.waiting_sum)}
              </div>
            </div>
            <div className="card">
              <div className="label">Ombor</div>
              <div className="value">{stats.warehouse.units.toLocaleString()}</div>
              <p className="muted-sm">
                +{stats.warehouse.today_in} / −{stats.warehouse.today_out}
              </p>
            </div>
          </div>

          {stats.daily.top?.length ? (
            <section className="section">
              <h2>Bugungi top mahsulotlar</h2>
              <div className="list">
                {stats.daily.top.map((t) => (
                  <div key={t.product_name} className="item row-between">
                    <h3>{t.product_name}</h3>
                    <span className="mono">{t.qty} dona</span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : null}

      {tab === 'orders' ? (
        <section className="section">
          <h2>Buyurtmalar</h2>
          <div className="field">
            <label>Qidiruv (ID / telefon)</label>
            <input
              value={orderQuery}
              onChange={(e) => setOrderQuery(e.target.value)}
              placeholder="masalan 102 yoki 90..."
            />
          </div>
          <div className="tabs-inline">
            {ORDER_FILTERS.map(([k, label]) => (
              <button
                key={k}
                type="button"
                className={`chip${orderStatus === k ? ' active' : ''}`}
                onClick={() => setOrderStatus(k)}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="list">
            {orders.length === 0 ? (
              <div className="empty">Buyurtma yo‘q</div>
            ) : (
              orders.map((o) => renderOrderCard(o))
            )}
          </div>
        </section>
      ) : null}

      {tab === 'payments' ? (
        <section className="section">
          <h2>To‘lovlar (karta)</h2>
          <p className="sub" style={{ marginBottom: 12 }}>
            Mijoz karta orqali to‘lov yuborgan buyurtmalar
          </p>
          <div className="list">
            {payments.length === 0 ? (
              <div className="empty">Kutayotgan to‘lov yo‘q</div>
            ) : (
              payments.map((o) => renderOrderCard(o, true))
            )}
          </div>
        </section>
      ) : null}

      {tab === 'warehouse' ? (
        <section className="section">
          <div className="row-between" style={{ marginBottom: 10 }}>
            <h2 style={{ margin: 0 }}>Ombor</h2>
            <button
              type="button"
              className={`chip${lowOnly ? ' active' : ''}`}
              onClick={() => setLowOnly((v) => !v)}
            >
              Faqat kam qoldiq
            </button>
          </div>
          <div className="card" style={{ marginBottom: 12 }}>
            <div className="field">
              <label>Amal</label>
              <select
                value={stockForm.mode}
                onChange={(e) =>
                  setStockForm((s) => ({ ...s, mode: e.target.value }))
                }
              >
                <option value="in">📥 Kirim</option>
                <option value="out">📤 Chiqim</option>
                <option value="inventory">📋 Inventar</option>
              </select>
            </div>
            <div className="field">
              <label>Mahsulot</label>
              <select
                value={stockForm.product_id || ''}
                onChange={(e) =>
                  setStockForm((s) => ({
                    ...s,
                    product_id: Number(e.target.value),
                  }))
                }
              >
                <option value="">Tanlang</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.category_name} · {p.name} ({p.stock})
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Miqdor</label>
              <input
                type="number"
                min={0}
                value={stockForm.qty}
                onChange={(e) =>
                  setStockForm((s) => ({ ...s, qty: Number(e.target.value) }))
                }
              />
            </div>
            <div className="field">
              <label>Izoh</label>
              <input
                value={stockForm.note}
                onChange={(e) =>
                  setStockForm((s) => ({ ...s, note: e.target.value }))
                }
                placeholder="ixtiyoriy"
              />
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void submitStock()}
            >
              Saqlash
            </button>
          </div>

          <div className="tabs-inline">
            <button
              type="button"
              className={`chip${selectedCat === 'all' ? ' active' : ''}`}
              onClick={() => setSelectedCat('all')}
            >
              Hammasi
            </button>
            {categories.map((c) => (
              <button
                key={c.category_id}
                type="button"
                className={`chip${selectedCat === c.category_id ? ' active' : ''}`}
                onClick={() => setSelectedCat(c.category_id)}
              >
                {c.category_name}
                {c.low_count ? ` · ${c.low_count}` : ''}
              </button>
            ))}
          </div>
          <div className="list">
            {filteredProducts.map((p) => (
              <div key={p.id} className="item">
                <div className="row-between">
                  <div>
                    <h3>{p.name}</h3>
                    <p>
                      {p.category_name} · {money(p.price)}
                    </p>
                  </div>
                  <div className="mono value" style={{ fontSize: '1.1rem' }}>
                    {p.stock}
                  </div>
                </div>
                <div className="actions">
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void quickIn(p.id, 1)}
                  >
                    +1
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void quickIn(p.id, 10)}
                  >
                    +10
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() =>
                      setStockForm({
                        product_id: p.id,
                        mode: 'in',
                        qty: 1,
                        note: '',
                      })
                    }
                  >
                    Forma
                  </button>
                </div>
              </div>
            ))}
            {filteredProducts.length === 0 ? (
              <div className="empty">Mahsulot yo‘q</div>
            ) : null}
          </div>
        </section>
      ) : null}

      {tab === 'moves' ? (
        <section className="section">
          <h2>Harakatlar</h2>
          <div className="list">
            {moves.length === 0 ? (
              <div className="empty">Harakat yo‘q</div>
            ) : (
              moves.map((m) => (
                <div key={m.id} className="item">
                  <div className="row-between">
                    <h3>{m.product_name}</h3>
                    <span className="badge">
                      {REASON[m.reason] || m.reason}
                    </span>
                  </div>
                  <p className="mono">
                    {m.delta > 0 ? `+${m.delta}` : m.delta} → {m.stock_after}
                    {m.note ? ` · ${m.note}` : ''}
                  </p>
                  <p>{m.created_at}</p>
                </div>
              ))
            )}
          </div>
        </section>
      ) : null}

      {tab === 'products' ? (
        <section className="section">
          <h2>Mahsulotlar</h2>
          <div className="list">
            {catalog.map((p) => (
              <div key={p.id} className="item">
                <div className="row-between">
                  <div>
                    <h3>
                      {p.is_active ? '✅' : '🚫'} {p.name}
                    </h3>
                    <p>
                      {p.category_name} · {p.stock} dona
                    </p>
                  </div>
                  <div className="mono">{money(p.price)}</div>
                </div>
                <div className="actions">
                  <input
                    className="price-input"
                    type="number"
                    min={0}
                    value={priceEdit[p.id] ?? String(p.price)}
                    onChange={(e) =>
                      setPriceEdit((s) => ({ ...s, [p.id]: e.target.value }))
                    }
                  />
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void savePrice(p)}
                  >
                    Narx
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => void toggleProduct(p)}
                  >
                    {p.is_active ? 'Yashirish' : 'Ko‘rsatish'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <nav className="nav" aria-label="Admin menyu">
        <div className="nav-inner">
          {(
            [
              ['dash', '📊', 'Home'],
              ['orders', '📦', 'Buyurtma'],
              ['payments', '💳', 'To‘lov'],
              ['warehouse', '🏭', 'Ombor'],
              ['moves', '📜', 'Jurnal'],
              ['products', '🛍', 'Tovar'],
            ] as const
          ).map(([id, ico, label]) => (
            <button
              key={id}
              type="button"
              className={`nav-btn${tab === id ? ' active' : ''}`}
              onClick={() => setTab(id)}
            >
              <span>{ico}</span>
              {label}
              {id === 'payments' && stats && stats.payments_waiting > 0 ? (
                <span className="nav-dot">{stats.payments_waiting}</span>
              ) : null}
            </button>
          ))}
        </div>
      </nav>
    </div>
  )
}
