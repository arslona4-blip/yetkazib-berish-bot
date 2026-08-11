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

function money(n: number) {
  return `${Number(n || 0).toLocaleString('uz-UZ')} so‘m`
}

export default function App() {
  const [auth, setAuth] = useState<AuthState | null>(() => loadAuth())
  const [tab, setTab] = useState<Tab>('dash')
  const [shop, setShop] = useState('Admin')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [stats, setStats] = useState<StatsPayload | null>(null)
  const [orderStatus, setOrderStatus] = useState('new')
  const [orders, setOrders] = useState<Order[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [selectedCat, setSelectedCat] = useState<number | 'all'>('all')
  const [moves, setMoves] = useState<Movement[]>([])
  const [stockForm, setStockForm] = useState({
    product_id: 0,
    mode: 'in',
    qty: 1,
    note: '',
  })
  const [pinForm, setPinForm] = useState({ adminId: '', pin: '' })

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

  async function refreshAll(a: AuthState | null = auth) {
    if (!a) return
    setBusy(true)
    setError('')
    try {
      const [st, or, cats, prods, mv] = await Promise.all([
        api.stats(a),
        api.orders(a, orderStatus),
        api.whCategories(a),
        api.whProducts(a),
        api.whMoves(a),
      ])
      setStats(st)
      setOrders(or.orders)
      setCategories(cats.categories)
      setProducts(prods.products)
      setMoves(mv.movements)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Yuklash xato')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    if (auth) void bootstrap(auth)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!auth) return
    void (async () => {
      try {
        const or = await api.orders(auth, orderStatus)
        setOrders(or.orders)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Buyurtmalar xato')
      }
    })()
  }, [orderStatus, auth])

  const filteredProducts = useMemo(() => {
    if (selectedCat === 'all') return products
    return products.filter((p) => p.category_id === selectedCat)
  }, [products, selectedCat])

  async function changeStatus(orderId: number, status: string) {
    if (!auth) return
    setBusy(true)
    try {
      await api.setStatus(auth, orderId, status)
      const or = await api.orders(auth, orderStatus)
      setOrders(or.orders)
      const st = await api.stats(auth)
      setStats(st)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Status xato')
    } finally {
      setBusy(false)
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
      const [prods, mv, st] = await Promise.all([
        api.whProducts(auth),
        api.whMoves(auth),
        api.stats(auth),
      ])
      setProducts(prods.products)
      setMoves(mv.movements)
      setStats(st)
      setStockForm((s) => ({ ...s, qty: 1, note: '' }))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ombor xato')
    } finally {
      setBusy(false)
    }
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
            Professional boshqaruv: buyurtmalar, ombor va hisobotlar. Telegramdan
            oching yoki Admin ID + PIN bilan kiring.
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
          <p className="sub">Professional boshqaruv paneli</p>
        </div>
        <div className="actions">
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
            <div className="card">
              <div className="label">Yangi</div>
              <div className="value accent">{stats.stats.new_orders}</div>
            </div>
            <div className="card">
              <div className="label">Faol</div>
              <div className="value">{stats.stats.active_orders}</div>
            </div>
            <div className="card">
              <div className="label">Bugun savdo</div>
              <div className="value warn mono">
                {money(stats.stats.today_sum)}
              </div>
            </div>
            <div className="card">
              <div className="label">Kam qoldiq</div>
              <div className="value warn">{stats.warehouse.low_stock}</div>
            </div>
          </div>
          <div className="section grid">
            <div className="card">
              <div className="label">Ombor birlik</div>
              <div className="value">{stats.warehouse.units.toLocaleString()}</div>
            </div>
            <div className="card">
              <div className="label">Bugun kirim / chiqim</div>
              <div className="value">
                +{stats.warehouse.today_in} / −{stats.warehouse.today_out}
              </div>
            </div>
          </div>
        </>
      ) : null}

      {tab === 'orders' ? (
        <section className="section">
          <h2>Buyurtmalar</h2>
          <div className="tabs-inline">
            {[
              ['new', 'Yangi'],
              ['active', 'Faol'],
              ['delivered', 'Yetkazilgan'],
              ['cancelled', 'Bekor'],
            ].map(([k, label]) => (
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
              orders.map((o) => (
                <article key={o.id} className="item">
                  <div className="row-between">
                    <h3>#{o.id} · {money(o.price)}</h3>
                    <span className="badge">{o.status_label}</span>
                  </div>
                  <p>
                    {o.phone} · {o.delivery_address}
                    {o.delivery_slot ? ` · ${o.delivery_slot}` : ''}
                  </p>
                  <div className="meta">
                    <span className="badge warn">{o.payment_label}</span>
                  </div>
                  <div className="actions">
                    {['accepted', 'in_delivery', 'delivered', 'cancelled'].map(
                      (st) => (
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
                      ),
                    )}
                  </div>
                </article>
              ))
            )}
          </div>
        </section>
      ) : null}

      {tab === 'warehouse' ? (
        <section className="section">
          <h2>Ombor</h2>
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
              </button>
            ))}
          </div>
          <div className="list">
            {filteredProducts.map((p) => (
              <div key={p.id} className="item row-between">
                <div>
                  <h3>{p.name}</h3>
                  <p>
                    {p.category_name} · {money(p.price)}
                  </p>
                </div>
                <div className="mono value" style={{ fontSize: '1.1rem' }}>
                  {p.stock}
                  <div>
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
                      Tanlash
                    </button>
                  </div>
                </div>
              </div>
            ))}
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
            {products.map((p) => (
              <div key={p.id} className="item row-between">
                <div>
                  <h3>
                    {p.is_active ? '✅' : '🚫'} {p.name}
                  </h3>
                  <p>
                    {p.category_name} · {money(p.price)}
                  </p>
                </div>
                <div className="mono">{p.stock} dona</div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <nav className="nav" aria-label="Admin menyu">
        <div className="nav-inner">
          {(
            [
              ['dash', '📊', 'Dashboard'],
              ['orders', '📦', 'Buyurtma'],
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
            </button>
          ))}
        </div>
      </nav>
    </div>
  )
}
